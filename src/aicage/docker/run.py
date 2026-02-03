import shlex
import subprocess
from pathlib import Path

from docker.errors import ContainerError, DockerException, ImageNotFound

from aicage.docker._client import get_docker_client
from aicage.docker._env import resolve_user_ids
from aicage.docker._mounts import append_mount
from aicage.docker.cli import run_docker_command
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


def _assemble_docker_run(args: DockerRunArgs) -> list[str]:
    cmd: list[str] = ["docker", "run", "--rm", "-it"]
    cmd.extend(resolve_user_ids())
    for env in args.env:
        cmd.extend(["-e", f"{env.name}={env.value}"])
    for mount in args.mounts:
        append_mount(cmd, mount.host_path, mount.container_path, read_only=mount.read_only)

    if args.merged_docker_args:
        cmd.extend(shlex.split(args.merged_docker_args))

    cmd.append(args.image_ref)
    cmd.extend(args.agent_args)
    return cmd
