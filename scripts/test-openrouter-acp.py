#!/usr/bin/env python3
"""Run the OpenRouter ACP smoke test for the agents configured by aicage."""

import hashlib
import json
import os
import queue
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep
from typing import Any

_API_KEY_ENV: str = "OPENROUTER_API_KEY"
_ARTIFACT_DIR_ENV: str = "AICAGE_OPENROUTER_ARTIFACT_DIR"
_PROMPT: str = "say hello"
_REQUEST_TIMEOUT_SECONDS: float = 600.0
_CLEANUP_ATTEMPTS: int = 20
_CLEANUP_RETRY_SECONDS: float = 0.25
_FAILURE_LOG_TAIL_BYTES: int = 16_384
_PROTOCOL_VERSION: int = 1
_JSON_RPC_VERSION: str = "2.0"
_CREATE_NEW_PROCESS_GROUP: int = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
_CTRL_BREAK_EVENT: int = getattr(signal, "CTRL_BREAK_EVENT", signal.SIGTERM)
_CONFIG_ROOT: Path = Path(__file__).resolve().parents[1] / "doc/ai/task/39/agent-config"
_MARKER_EXTENSION_SOURCE: Path = Path(__file__).resolve().parents[1] / "doc/sample/custom/extensions/marker"


@dataclass(frozen=True)
class _Agent:
    name: str
    config_source: Path
    config_destination: Path
    aicage_args: tuple[str, ...]


_AGENTS: tuple[_Agent, ...] = (
    _Agent(
        name="opencode",
        config_source=_CONFIG_ROOT / "opencode/opencode.json",
        config_destination=Path(".config/opencode/opencode.json"),
        aicage_args=("-e", _API_KEY_ENV, "--", "opencode", "acp"),
    ),
    _Agent(
        name="vibe",
        config_source=_CONFIG_ROOT / "vibe/config.toml",
        config_destination=Path(".vibe/config.toml"),
        aicage_args=(
            "-e",
            _API_KEY_ENV,
            "-e",
            "VIBE_ACTIVE_MODEL=openrouter-free",
            "-e",
            "AICAGE_ENTRYPOINT_CMD=vibe-acp",
            "--",
            "vibe",
        ),
    ),
)


class _AcpClient:
    def __init__(self, command: list[str], environment: dict[str, str], cwd: Path) -> None:
        popen_arguments: dict[str, Any] = {}
        if os.name == "nt":
            popen_arguments["creationflags"] = _CREATE_NEW_PROCESS_GROUP
        else:
            popen_arguments["start_new_session"] = True
        self._process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **popen_arguments,
        )
        self._messages: queue.Queue[dict[str, Any] | BaseException | None] = queue.Queue()
        self._stderr: list[bytes] = []
        self._next_request_id = 1
        self._response_chunks: list[str] = []
        self._start_reader(self._read_stdout)
        self._start_reader(self._read_stderr)

    def close(self) -> None:
        self._terminate_process_group(signal.SIGTERM)
        try:
            self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._terminate_process_group(signal.SIGKILL)
            self._process.wait()

    def stderr(self) -> str:
        return b"".join(self._stderr).decode("utf-8", errors="replace")

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        request_id = self._next_request_id
        self._next_request_id += 1
        self._send(
            {
                "jsonrpc": _JSON_RPC_VERSION,
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        deadline = monotonic() + _REQUEST_TIMEOUT_SECONDS
        while True:
            message = self._next_message(deadline)
            if message.get("id") == request_id and "result" in message:
                result = message["result"]
                if not isinstance(result, dict):
                    raise RuntimeError(f"ACP {method} returned a non-object result.")
                return result
            if message.get("id") == request_id and "error" in message:
                raise RuntimeError(f"ACP {method} failed: {message['error']}")
            self._handle_incoming(message)

    def response_text(self) -> str:
        return "".join(self._response_chunks)

    def _start_reader(self, target: Any) -> None:
        threading.Thread(target=target, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self._process.stdout is not None
        try:
            for line in self._process.stdout:
                self._messages.put(json.loads(line))
        except (OSError, json.JSONDecodeError) as exc:
            self._messages.put(exc)
        finally:
            self._messages.put(None)

    def _read_stderr(self) -> None:
        assert self._process.stderr is not None
        for line in self._process.stderr:
            self._stderr.append(line)

    def _next_message(self, deadline: float) -> dict[str, Any]:
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise TimeoutError("ACP request timed out.")
        try:
            item = self._messages.get(timeout=remaining)
        except queue.Empty as exc:
            raise TimeoutError("ACP request timed out.") from exc
        if item is None:
            raise RuntimeError("ACP agent closed its output stream.")
        if isinstance(item, BaseException):
            raise RuntimeError("Invalid ACP output.") from item
        return item

    def _handle_incoming(self, message: dict[str, Any]) -> None:
        if message.get("method") == "session/update":
            self._record_session_update(message.get("params"))
        if "id" in message and "method" in message:
            self._send(
                {
                    "jsonrpc": _JSON_RPC_VERSION,
                    "id": message["id"],
                    "error": {"code": -32601, "message": "Unsupported by smoke test"},
                }
            )

    def _record_session_update(self, params: object) -> None:
        if not isinstance(params, dict):
            return
        update = params.get("update")
        if not isinstance(update, dict) or update.get("sessionUpdate") != "agent_message_chunk":
            return
        content = update.get("content")
        if isinstance(content, dict) and content.get("type") == "text":
            text = content.get("text")
            if isinstance(text, str):
                self._response_chunks.append(text)

    def _send(self, message: dict[str, Any]) -> None:
        assert self._process.stdin is not None
        self._process.stdin.write(json.dumps(message).encode("utf-8") + b"\n")
        self._process.stdin.flush()

    def _terminate_process_group(self, termination_signal: signal.Signals) -> None:
        if os.name == "nt":
            if self._process.poll() is None:
                self._process.send_signal(_CTRL_BREAK_EVENT)
            return
        try:
            os.killpg(self._process.pid, termination_signal)
        except ProcessLookupError:
            pass


def main(argv: Sequence[str] | None = None) -> int:
    selected_agents = _select_agents(sys.argv[1:] if argv is None else argv)
    if selected_agents is None:
        return 2
    api_key = os.environ.get(_API_KEY_ENV)
    if not api_key:
        print(f"Set {_API_KEY_ENV} before running this test.", file=sys.stderr)
        return 2
    aicage_path = shutil.which("aicage")
    if not aicage_path:
        print("aicage must be available on PATH.", file=sys.stderr)
        return 2

    results = [_run_agent(agent, Path(aicage_path), api_key) for agent in selected_agents]
    return 0 if all(results) else 1


def _select_agents(agent_names: Sequence[str]) -> tuple[_Agent, ...] | None:
    if not agent_names:
        return _AGENTS
    agents_by_name = {agent.name: agent for agent in _AGENTS}
    unknown_names = [name for name in agent_names if name not in agents_by_name]
    if unknown_names:
        print(
            f"Unknown agent: {', '.join(unknown_names)}. Configured agents: {', '.join(agents_by_name)}.",
            file=sys.stderr,
        )
        return None
    return tuple(agents_by_name[name] for name in agent_names)


def _run_agent(agent: _Agent, aicage_path: Path, api_key: str) -> bool:
    temporary_root = Path(tempfile.mkdtemp(prefix=f"aicage-openrouter-{agent.name}-"))
    home_dir = temporary_root / "home"
    client: _AcpClient | None = None
    response = ""
    failure: Exception | None = None
    try:
        workspace = temporary_root / "workspace"
        workspace.mkdir()
        _write_agent_config(agent, home_dir)
        _write_marker_extension_config(agent, home_dir, workspace)
        _copy_docker_cli_plugins(home_dir)
        environment = _test_environment(home_dir, api_key)
        command = [str(aicage_path), "--menu", "none", *agent.aicage_args]
        client = _AcpClient(command, environment, workspace)
        _prompt_agent(client, workspace)
        response = client.response_text()
    except (OSError, RuntimeError, TimeoutError) as exc:
        failure = exc
    finally:
        if client is not None:
            client.close()

    if failure is not None:
        print(f"{agent.name}: FAIL: {failure}", file=sys.stderr)
        if client is not None:
            _print_stderr(client.stderr())
        _print_image_logs(home_dir)
        _copy_aicage_logs(home_dir, agent.name)
        print(f"{agent.name}: retained failed test home at {temporary_root}", file=sys.stderr)
        return False
    cleanup_error = _remove_temporary_root(temporary_root)
    if cleanup_error is not None:
        print(f"{agent.name}: FAIL: could not remove {temporary_root}: {cleanup_error}", file=sys.stderr)
        return False

    print(f"{agent.name}: {response}")
    if "hello" not in response.casefold():
        print(f"{agent.name}: FAIL: response did not contain 'hello'.", file=sys.stderr)
        return False
    print(f"{agent.name}: PASS")
    return True


def _write_agent_config(agent: _Agent, home_dir: Path) -> None:
    destination = home_dir / agent.config_destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(agent.config_source.read_text(encoding="utf-8"), encoding="utf-8")


def _write_marker_extension_config(agent: _Agent, home_dir: Path, workspace: Path) -> None:
    extension_dir = home_dir / ".aicage-custom/extensions/marker"
    extension_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(_MARKER_EXTENSION_SOURCE, extension_dir)
    (home_dir / ".aicage-test-share").mkdir(parents=True)
    config_dir = home_dir / ".aicage/projects"
    project_hash = hashlib.sha256(str(workspace.resolve()).encode("utf-8")).hexdigest()
    project_config = config_dir / f"{project_hash}.yml"
    project_config.parent.mkdir(parents=True, exist_ok=True)
    project_config.write_text(
        "agents:\n"
        f"  {agent.name}:\n"
        "    base: ubuntu\n"
        f"    image_ref: aicage-extended:{agent.name}-ubuntu-marker\n"
        "    extensions:\n"
        "      - marker\n",
        encoding="utf-8",
    )


def _copy_docker_cli_plugins(home_dir: Path) -> None:
    source = _host_docker_config_dir() / "cli-plugins"
    if source.is_dir():
        shutil.copytree(source, home_dir / ".docker/cli-plugins", symlinks=True)


def _host_docker_config_dir() -> Path:
    configured_directory = os.environ.get("DOCKER_CONFIG")
    if configured_directory:
        return Path(configured_directory)
    return Path(os.environ.get("HOME", str(Path.home()))) / ".docker"


def _remove_temporary_root(temporary_root: Path) -> OSError | None:
    cleanup_error: OSError | None = None
    for _ in range(_CLEANUP_ATTEMPTS):
        try:
            _make_temporary_tree_writable(temporary_root)
            shutil.rmtree(temporary_root)
            return None
        except OSError as exc:
            cleanup_error = exc
            sleep(_CLEANUP_RETRY_SECONDS)
    return cleanup_error


def _make_temporary_tree_writable(temporary_root: Path) -> None:
    for directory, directory_names, file_names in os.walk(temporary_root):
        directory_path = Path(directory)
        _add_owner_permissions(directory_path, stat.S_IWUSR | stat.S_IXUSR)
        for name in directory_names:
            _add_owner_permissions(directory_path / name, stat.S_IWUSR | stat.S_IXUSR)
        for name in file_names:
            _add_owner_permissions(directory_path / name, stat.S_IWUSR)


def _add_owner_permissions(path: Path, permissions: int) -> None:
    if path.is_symlink():
        return
    path.chmod(path.stat().st_mode | permissions)


def _test_environment(home_dir: Path, api_key: str) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(home_dir),
            "XDG_CACHE_HOME": str(home_dir / ".cache"),
            "XDG_CONFIG_HOME": str(home_dir / ".config"),
            "XDG_DATA_HOME": str(home_dir / ".local/share"),
            "XDG_STATE_HOME": str(home_dir / ".local/state"),
            "DOCKER_CONFIG": str(home_dir / ".docker"),
            "USERPROFILE": str(home_dir),
            "APPDATA": str(home_dir / "AppData/Roaming"),
            "LOCALAPPDATA": str(home_dir / "AppData/Local"),
            _API_KEY_ENV: api_key,
        }
    )
    return environment


def _prompt_agent(client: _AcpClient, workspace: Path) -> None:
    client.request(
        "initialize",
        {
            "protocolVersion": _PROTOCOL_VERSION,
            "clientCapabilities": {},
            "clientInfo": {"name": "aicage-openrouter-smoke-test", "version": "1"},
        },
    )
    session = client.request("session/new", {"cwd": str(workspace), "mcpServers": []})
    session_id = session.get("sessionId")
    if not isinstance(session_id, str):
        raise RuntimeError("ACP session/new did not return a session ID.")
    client.request(
        "session/prompt",
        {
            "sessionId": session_id,
            "prompt": [{"type": "text", "text": _PROMPT}],
        },
    )


def _print_stderr(stderr: str) -> None:
    if stderr:
        print(stderr.rstrip(), file=sys.stderr)


def _print_image_logs(home_dir: Path) -> None:
    log_directory = home_dir / ".aicage/logs/image"
    for log_path in sorted(log_directory.rglob("*.log")):
        contents = log_path.read_bytes()
        tail = contents[-_FAILURE_LOG_TAIL_BYTES:].decode("utf-8", errors="replace")
        print(f"[aicage] Image log {log_path.relative_to(home_dir)}:", file=sys.stderr)
        print(tail.rstrip(), file=sys.stderr)


def _copy_aicage_logs(home_dir: Path, agent_name: str) -> None:
    artifact_directory = os.environ.get(_ARTIFACT_DIR_ENV)
    source = home_dir / ".aicage"
    if not artifact_directory or not source.is_dir():
        return
    destination = Path(artifact_directory) / agent_name
    try:
        shutil.copytree(source, destination, symlinks=True)
    except OSError as exc:
        print(f"{agent_name}: could not collect aicage logs: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
