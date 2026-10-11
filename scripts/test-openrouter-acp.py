#!/usr/bin/env python3
"""Run the OpenRouter ACP smoke test for the agents configured by aicage."""

import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

_API_KEY_ENV: str = "OPENROUTER_API_KEY"
_PROMPT: str = "say hello"
_REQUEST_TIMEOUT_SECONDS: float = 600.0
_PROTOCOL_VERSION: int = 1
_JSON_RPC_VERSION: str = "2.0"
_CONFIG_ROOT: Path = Path(__file__).resolve().parents[1] / "doc/ai/task/39/agent-config"


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
        self._process = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._messages: queue.Queue[dict[str, Any] | BaseException | None] = queue.Queue()
        self._stderr: list[bytes] = []
        self._next_request_id = 1
        self._response_chunks: list[str] = []
        self._start_reader(self._read_stdout)
        self._start_reader(self._read_stderr)

    def close(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
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


def main() -> int:
    api_key = os.environ.get(_API_KEY_ENV)
    if not api_key:
        print(f"Set {_API_KEY_ENV} before running this test.", file=sys.stderr)
        return 2
    aicage_path = shutil.which("aicage")
    if not aicage_path:
        print("aicage must be available on PATH.", file=sys.stderr)
        return 2

    results = [_run_agent(agent, Path(aicage_path), api_key) for agent in _AGENTS]
    return 0 if all(results) else 1


def _run_agent(agent: _Agent, aicage_path: Path, api_key: str) -> bool:
    with tempfile.TemporaryDirectory(prefix=f"aicage-openrouter-{agent.name}-") as temp_dir:
        temporary_root = Path(temp_dir)
        home_dir = temporary_root / "home"
        workspace = temporary_root / "workspace"
        workspace.mkdir()
        _write_agent_config(agent, home_dir)
        environment = _test_environment(home_dir, api_key)
        command = [str(aicage_path), "--menu", "none", *agent.aicage_args]
        client = _AcpClient(command, environment, workspace)
        try:
            _prompt_agent(client, workspace)
            response = client.response_text()
        except (OSError, RuntimeError, TimeoutError) as exc:
            print(f"{agent.name}: FAIL: {exc}", file=sys.stderr)
            _print_stderr(client.stderr())
            return False
        finally:
            client.close()

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


def _test_environment(home_dir: Path, api_key: str) -> dict[str, str]:
    environment = dict(os.environ)
    environment.update(
        {
            "HOME": str(home_dir),
            "XDG_CACHE_HOME": str(home_dir / ".cache"),
            "XDG_CONFIG_HOME": str(home_dir / ".config"),
            "XDG_DATA_HOME": str(home_dir / ".local/share"),
            "XDG_STATE_HOME": str(home_dir / ".local/state"),
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


if __name__ == "__main__":
    raise SystemExit(main())
