from pathlib import Path, PurePosixPath
from unittest import TestCase

from aicage.docker.execution.mounts import (
    _format_mount_value,
    append_mount,
    append_volume_mount,
)


class MountsTests(TestCase):
    def test_format_mount_value_rw(self) -> None:
        value = _format_mount_value(
            Path("/host"),
            PurePosixPath("/container"),
            read_only=False,
        )
        self.assertEqual("type=bind,src=/host,dst=/container", value)

    def test_format_mount_value_ro(self) -> None:
        value = _format_mount_value(
            Path("/host"),
            PurePosixPath("/container"),
            read_only=True,
        )
        self.assertEqual("type=bind,src=/host,dst=/container,readonly", value)

    def test_append_mount_adds_args(self) -> None:
        cmd: list[str] = ["docker", "run"]
        append_mount(
            cmd,
            Path("/host"),
            PurePosixPath("/container"),
            read_only=True,
        )
        self.assertEqual(
            ["docker", "run", "--mount", "type=bind,src=/host,dst=/container,readonly"],
            cmd,
        )

    def test_append_volume_mount_adds_args(self) -> None:
        cmd: list[str] = ["docker", "run"]
        append_volume_mount(
            cmd,
            "aicage-ssh-agent-socket",
            PurePosixPath("/run/aicage-credential-agent"),
            read_only=True,
        )
        self.assertEqual(
            [
                "docker",
                "run",
                "--mount",
                "type=volume,src=aicage-ssh-agent-socket,dst=/run/aicage-credential-agent,readonly",
            ],
            cmd,
        )
