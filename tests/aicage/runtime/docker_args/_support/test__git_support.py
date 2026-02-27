import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.paths import HOST_GNUPG_DIR, HOST_SSH_DIR
from aicage.runtime.docker_args._support import _git_support

_MODULE = "aicage.runtime.docker_args._support._git_support"


class GitSupportTests(TestCase):
    def test_resolve_git_config_path_parses_first_file(self) -> None:
        output = "file:/home/user/.gitconfig user.name=Name\nfile:/tmp/other key=value\n"
        with mock.patch(f"{_MODULE}.capture_stdout", return_value=output):
            path = _git_support.resolve_git_config_path()
        self.assertEqual(Path("/home/user/.gitconfig"), path)

    def test_resolve_git_config_path_handles_empty(self) -> None:
        with mock.patch(f"{_MODULE}.capture_stdout", return_value=""):
            path = _git_support.resolve_git_config_path()
        self.assertIsNone(path)

    def test_resolve_git_root_prefers_superproject(self) -> None:
        project_path = Path("/tmp/project")
        superproject = "/tmp/root"
        with mock.patch(
            f"{_MODULE}.capture_stdout",
            return_value=f"{superproject}\n",
        ) as capture_mock:
            result = _git_support.resolve_git_root(project_path)
        self.assertEqual(Path(superproject).resolve(), result)
        capture_mock.assert_called_once_with(
            ["git", "rev-parse", "--show-superproject-working-tree"],
            cwd=project_path,
        )

    def test_resolve_git_root_falls_back_to_toplevel(self) -> None:
        project_path = Path("/tmp/project")
        toplevel = "/tmp/root"
        with mock.patch(
            f"{_MODULE}.capture_stdout",
            side_effect=["", f"{toplevel}\n"],
        ) as capture_mock:
            result = _git_support.resolve_git_root(project_path)
        self.assertEqual(Path(toplevel).resolve(), result)
        self.assertEqual(2, capture_mock.call_count)

    def test_resolve_gpg_home_parses_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            gpg_home = Path(tmp_dir) / HOST_GNUPG_DIR.name
            gpg_home.mkdir()
            with mock.patch(
                f"{_MODULE}.capture_stdout",
                return_value=f"{gpg_home}\n",
            ):
                path = _git_support.resolve_gpg_home()
        self.assertEqual(gpg_home, path)

    def test_resolve_gpg_home_falls_back_to_home_gnupg(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            gpg_home = Path(tmp_dir) / HOST_GNUPG_DIR.name
            gpg_home.mkdir()
            with (
                mock.patch(f"{_MODULE}.HOST_GNUPG_DIR", gpg_home),
                mock.patch(f"{_MODULE}.capture_stdout", return_value=""),
            ):
                path = _git_support.resolve_gpg_home()
        self.assertEqual(gpg_home, path)

    def test_resolve_gpg_home_handles_missing_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with (
                mock.patch(f"{_MODULE}.HOST_GNUPG_DIR", Path(tmp_dir) / HOST_GNUPG_DIR.name),
                mock.patch(f"{_MODULE}.capture_stdout", return_value=""),
            ):
                path = _git_support.resolve_gpg_home()
        self.assertIsNone(path)

    def test_resolve_ssh_dir_uses_home(self) -> None:
        ssh_dir = Path("/home/user") / HOST_SSH_DIR.name
        with mock.patch(f"{_MODULE}.HOST_SSH_DIR", ssh_dir):
            path = _git_support.resolve_ssh_dir()
        self.assertEqual(ssh_dir, path)

    def test_uses_ssh_remotes_detects_scp_style_url(self) -> None:
        with mock.patch(
            f"{_MODULE}.capture_stdout",
            return_value="origin git@github.com:aicage/aicage.git (fetch)\n",
        ):
            self.assertTrue(_git_support.uses_ssh_remotes(Path("/repo")))

    def test_uses_ssh_remotes_detects_ssh_scheme_url(self) -> None:
        with mock.patch(
            f"{_MODULE}.capture_stdout",
            return_value="origin ssh://git@github.com/aicage/aicage.git (fetch)\n",
        ):
            self.assertTrue(_git_support.uses_ssh_remotes(Path("/repo")))

    def test_uses_ssh_remotes_skips_https_url(self) -> None:
        with mock.patch(
            f"{_MODULE}.capture_stdout",
            return_value="origin https://github.com/aicage/aicage.git (fetch)\n",
        ):
            self.assertFalse(_git_support.uses_ssh_remotes(Path("/repo")))

    def test_uses_ssh_remotes_handles_empty_output(self) -> None:
        with mock.patch(f"{_MODULE}.capture_stdout", return_value=""):
            self.assertFalse(_git_support.uses_ssh_remotes(Path("/repo")))

    def test_resolve_git_support_prefs_sets_relevant_prefs(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        project_path = Path("/repo")
        git_root = Path("/repo/root")

        with tempfile.TemporaryDirectory() as tmp_dir:
            git_config = Path(tmp_dir) / ".gitconfig"
            git_config.write_text("user.name = tester", encoding="utf-8")
            gpg_home = Path(tmp_dir) / "gnupg"
            gpg_home.mkdir()

            with (
                mock.patch(f"{_MODULE}.resolve_git_config_path", return_value=git_config),
                mock.patch(f"{_MODULE}.resolve_git_root", return_value=git_root),
                mock.patch(f"{_MODULE}.resolve_gpg_home", return_value=gpg_home),
                mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=True),
                mock.patch(f"{_MODULE}.resolve_signing_format", return_value="gpg"),
                mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
                mock.patch(
                    f"{_MODULE}.prompt_mount_git_support",
                    return_value=["gitconfig", "gitroot", "gnupg"],
                ),
            ):
                _git_support.resolve_git_support_prefs(project_path, agent_cfg)

        self.assertTrue(agent_cfg.mounts.gitconfig)
        self.assertTrue(agent_cfg.mounts.gitroot)
        self.assertTrue(agent_cfg.mounts.gnupg)

    def test_resolve_git_support_prefs_defaults_to_gpg_when_format_missing(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        project_path = Path("/repo")
        git_root = Path("/repo/root")

        with tempfile.TemporaryDirectory() as tmp_dir:
            gpg_home = Path(tmp_dir) / "gnupg"
            gpg_home.mkdir()
            git_config = Path(tmp_dir) / ".gitconfig"
            git_config.write_text("user.name = tester", encoding="utf-8")

            with (
                mock.patch(f"{_MODULE}.resolve_git_config_path", return_value=git_config),
                mock.patch(f"{_MODULE}.resolve_git_root", return_value=git_root),
                mock.patch(f"{_MODULE}.resolve_gpg_home", return_value=gpg_home),
                mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=True),
                mock.patch(f"{_MODULE}.resolve_signing_format", return_value=None),
                mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
                mock.patch(f"{_MODULE}.prompt_mount_git_support", return_value=["gnupg"]),
            ):
                _git_support.resolve_git_support_prefs(project_path, agent_cfg)

        self.assertTrue(agent_cfg.mounts.gnupg)

    def test_resolve_git_support_prefs_sets_unselected_values_false(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        project_path = Path("/repo")
        git_root = Path("/repo/root")

        with tempfile.TemporaryDirectory() as tmp_dir:
            git_config = Path(tmp_dir) / ".gitconfig"
            git_config.write_text("user.name = tester", encoding="utf-8")
            gpg_home = Path(tmp_dir) / "gnupg"
            gpg_home.mkdir()

            with (
                mock.patch(f"{_MODULE}.resolve_git_config_path", return_value=git_config),
                mock.patch(f"{_MODULE}.resolve_git_root", return_value=git_root),
                mock.patch(f"{_MODULE}.resolve_gpg_home", return_value=gpg_home),
                mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=True),
                mock.patch(f"{_MODULE}.resolve_signing_format", return_value="gpg"),
                mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
                mock.patch(f"{_MODULE}.prompt_mount_git_support", return_value=["gitconfig"]),
            ):
                _git_support.resolve_git_support_prefs(project_path, agent_cfg)

        self.assertTrue(agent_cfg.mounts.gitconfig)
        self.assertFalse(agent_cfg.mounts.gitroot)
        self.assertFalse(agent_cfg.mounts.gnupg)

    @staticmethod
    def test_resolve_git_support_prefs_skips_when_no_items() -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts(gitconfig=True, gitroot=False, gnupg=False, ssh=False))
        project_path = Path("/repo")

        with (
            mock.patch(f"{_MODULE}.resolve_git_config_path", return_value=None),
            mock.patch(f"{_MODULE}.resolve_git_root", return_value=project_path),
            mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=False),
            mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=False),
            mock.patch(f"{_MODULE}.prompt_mount_git_support") as prompt_mock,
        ):
            _git_support.resolve_git_support_prefs(project_path, agent_cfg)

        prompt_mock.assert_not_called()

    def test_resolve_git_support_prefs_includes_ssh_for_ssh_remotes(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        project_path = Path("/repo")

        with tempfile.TemporaryDirectory() as tmp_dir:
            ssh_dir = Path(tmp_dir) / "ssh"
            ssh_dir.mkdir()

            with (
                mock.patch(f"{_MODULE}.resolve_git_config_path", return_value=None),
                mock.patch(f"{_MODULE}.resolve_git_root", return_value=project_path),
                mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=False),
                mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=True),
                mock.patch(f"{_MODULE}.resolve_ssh_dir", return_value=ssh_dir),
                mock.patch(f"{_MODULE}.prompt_mount_git_support", return_value=["ssh"]),
            ):
                _git_support.resolve_git_support_prefs(project_path, agent_cfg)

        self.assertTrue(agent_cfg.mounts.ssh)

    def test_resolve_git_support_prefs_includes_ssh_and_gnupg_when_both_needed(self) -> None:
        agent_cfg = AgentConfig(mounts=_AgentMounts())
        project_path = Path("/repo")

        with tempfile.TemporaryDirectory() as tmp_dir:
            ssh_dir = Path(tmp_dir) / "ssh"
            ssh_dir.mkdir()
            gpg_home = Path(tmp_dir) / "gnupg"
            gpg_home.mkdir()

            with (
                mock.patch(f"{_MODULE}.resolve_git_config_path", return_value=None),
                mock.patch(f"{_MODULE}.resolve_git_root", return_value=project_path),
                mock.patch(f"{_MODULE}.is_commit_signing_enabled", return_value=True),
                mock.patch(f"{_MODULE}.resolve_signing_format", return_value="gpg"),
                mock.patch(f"{_MODULE}.uses_ssh_remotes", return_value=True),
                mock.patch(f"{_MODULE}.resolve_ssh_dir", return_value=ssh_dir),
                mock.patch(f"{_MODULE}.resolve_gpg_home", return_value=gpg_home),
                mock.patch(f"{_MODULE}.prompt_mount_git_support", return_value=["ssh", "gnupg"]) as prompt_mock,
            ):
                _git_support.resolve_git_support_prefs(project_path, agent_cfg)

        items = prompt_mock.call_args.args[0]
        keys = [item[0] for item in items]
        self.assertIn("ssh", keys)
        self.assertIn("gnupg", keys)
        self.assertTrue(agent_cfg.mounts.ssh)
        self.assertTrue(agent_cfg.mounts.gnupg)
