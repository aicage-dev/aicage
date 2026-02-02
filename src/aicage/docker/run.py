import os
import shlex
import subprocess
from pathlib import Path, PurePosixPath

from docker.errors import ContainerError, DockerException, ImageNotFound

from aicage.docker._client import get_docker_client
from aicage.docker.cli import run_docker_command
from aicage.paths import CONTAINER_WORKSPACE_DIR, container_project_path
from aicage.runtime.env_vars import AICAGE_GID, AICAGE_UID, AICAGE_USER, AICAGE_WORKSPACE
from aicage.runtime.run_args import DockerRunArgs


def run_container(args: DockerRunArgs) -> None:
    command = _assemble_docker_run(args)
    run_docker_command(command, check=True)


def print_run_command(args: DockerRunArgs) -> None:
    command = _assemble_docker_run(args)
    print(shlex.join(command))


def run_builder_version_check(image_ref: str, definition_dir: Path) -> subprocess.CompletedProcess[str]:
    command = [
        "/bin/bash",
        "-c",
        "cp /agent/version.sh /tmp/version.sh "
        "&& sed -i 's/\\r$//' /tmp/version.sh "
        "&& chmod +x /tmp/version.sh "
        "&& /bin/bash /tmp/version.sh",
    ]
    volume_src = str(definition_dir.resolve())
    client = get_docker_client()
    try:
        output = client.containers.run(
            image=image_ref,
            command=command,
            volumes={volume_src: {"bind": "/agent", "mode": "ro"}},
            working_dir="/agent",
            remove=True,
            stdout=True,
            stderr=True,
        )
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")
    except ContainerError as exc:
        stdout = _decode_container_output(getattr(exc, "stdout", ""))
        stderr = _decode_container_output(getattr(exc, "stderr", ""))
        return subprocess.CompletedProcess(command, exc.exit_status, stdout=stdout, stderr=stderr)
    except (ImageNotFound, DockerException) as exc:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr=str(exc))


def _decode_container_output(output: object) -> str:
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    if isinstance(output, str):
        return output
    return ""


def _resolve_user_ids() -> list[str]:
    env_flags: list[str] = []
    if os.name == "nt":
        user = "root"
        env_flags.extend(["-e", f"{AICAGE_USER}={user}"])
        return env_flags

    getuid = getattr(os, "getuid", None)
    getgid = getattr(os, "getgid", None)
    uid = getuid() if callable(getuid) else None
    gid = getgid() if callable(getgid) else None

    user = os.environ.get("USER") or os.environ.get("USERNAME") or "aicage"
    if uid is not None:
        env_flags.extend(["-e", f"{AICAGE_UID}={uid}", "-e", f"{AICAGE_GID}{'='}{gid}"])
    env_flags.extend(["-e", f"{AICAGE_USER}={user}"])
    return env_flags


def _assemble_docker_run(args: DockerRunArgs) -> list[str]:
    cmd: list[str] = ["docker", "run", "--rm", "-it"]
    cmd.extend(_resolve_user_ids())
    project_container_path = container_project_path(args.project_path)
    cmd.extend(["-e", f"{AICAGE_WORKSPACE}={project_container_path.as_posix()}"])
    for env in args.env:
        cmd.extend(["-e", f"{env.name}={env.value}"])
    _append_mount(cmd, args.project_path, CONTAINER_WORKSPACE_DIR, read_only=False)
    _append_mount(cmd, args.project_path, project_container_path, read_only=False)
    for mount in args.agent_config_mounts:
        _append_mount(cmd, mount.host_path, mount.container_path, read_only=False)
    for mount in args.mounts:
        _append_mount(cmd, mount.host_path, mount.container_path, read_only=mount.read_only)

    if args.merged_docker_args:
        cmd.extend(shlex.split(args.merged_docker_args))

    cmd.append(args.image_ref)
    cmd.extend(args.agent_args)
    return cmd


def _append_mount(
    cmd: list[str],
    host_path: Path,
    container_path: PurePosixPath,
    *,
    read_only: bool,
) -> None:
    mount_value = _format_mount_value(host_path, container_path, read_only=read_only)
    cmd.extend(["--mount", mount_value])


def _format_mount_value(
    host_path: Path,
    container_path: PurePosixPath,
    *,
    read_only: bool,
) -> str:
    parts = [
        "type=bind",
        f"src={host_path}",
        f"dst={container_path.as_posix()}",
    ]
    if read_only:
        parts.append("readonly")
    return ",".join(parts)
