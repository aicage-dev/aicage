from pathlib import Path, PurePosixPath
from unittest import TestCase

from aicage.docker.execution.mounts import mount_args
from aicage.runtime.run_args import BindMountSpec, MountSpec, VolumeMountSpec


class UnsupportedMountSpec(MountSpec):
    pass


class MountsTests(TestCase):
    def test_mount_args_returns_a_read_write_bind_mount(self) -> None:
        args = mount_args([BindMountSpec(Path("/host"), PurePosixPath("/container"))])
        self.assertEqual(["--mount", "type=bind,src=/host,dst=/container"], args)

    def test_mount_args_returns_a_read_only_bind_mount(self) -> None:
        args = mount_args(
            [BindMountSpec(Path("/host"), PurePosixPath("/container"), read_only=True)]
        )
        self.assertEqual(
            ["--mount", "type=bind,src=/host,dst=/container,readonly"], args
        )

    def test_mount_args_returns_a_read_only_volume_mount(self) -> None:
        args = mount_args(
            [
                VolumeMountSpec(
                    "aicage-credential-agent-ssh-socket",
                    PurePosixPath("/run/credential-agent"),
                    read_only=True,
                )
            ]
        )
        self.assertEqual(
            [
                "--mount",
                "type=volume,src=aicage-credential-agent-ssh-socket,"
                "dst=/run/credential-agent,readonly",
            ],
            args,
        )

    def test_mount_args_rejects_an_unsupported_mount_type(self) -> None:
        with self.assertRaisesRegex(
            TypeError, "Unsupported mount specification: UnsupportedMountSpec"
        ):
            mount_args([UnsupportedMountSpec()])
