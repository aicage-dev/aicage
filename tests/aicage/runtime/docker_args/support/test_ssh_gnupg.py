from pathlib import Path
from unittest import TestCase, mock

from aicage.config.project_config import _AgentMounts
from aicage.runtime.docker_args.support import ssh_gnupg


class SshGnuPgTests(TestCase):
    def test_ssh_gnupg_mount_defaults_respects_saved_choices(self) -> None:
        mounts = _AgentMounts(ssh=False)
        with (
            mock.patch(
                "aicage.runtime.docker_args.support.ssh_gnupg._has_ssh_keys",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.docker_args.support.ssh_gnupg.has_gpg_keys",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.docker_args.support.ssh_gnupg.resolve_gpg_home",
                return_value=Path("/test-tmp/gnupg"),
            ),
        ):
            self.assertEqual({"gnupg"}, ssh_gnupg.ssh_gnupg_mount_defaults(mounts))
