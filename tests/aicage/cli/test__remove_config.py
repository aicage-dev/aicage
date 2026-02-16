import io
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli import _remove_config as remove_config
from aicage.config.project_config import AgentConfig, ProjectConfig


class RemoveConfigTests(TestCase):
    def test_remove_project_config_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            with (
                mock.patch("aicage.cli._remove_config.SettingsStore", return_value=store),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_project_config()

        output = stdout.getvalue()
        self.assertIn("Project config not found:", output)
        self.assertIn(str(config_path), output)

    def test_remove_project_config_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            config_path.write_text("agents: {}", encoding="utf-8")
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            with (
                mock.patch("aicage.cli._remove_config.SettingsStore", return_value=store),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_project_config()

        output = stdout.getvalue()
        self.assertIn("Project config removed:", output)
        self.assertIn(str(config_path), output)
        self.assertFalse(config_path.exists())

    def test_remove_project_config_agent_missing_project_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            with (
                mock.patch("aicage.cli._remove_config.SettingsStore", return_value=store),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_project_config("codex")

        output = stdout.getvalue()
        self.assertIn("Project config not found:", output)
        self.assertIn(str(config_path), output)

    def test_remove_project_config_agent_missing_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            config_path.write_text("agents: {}", encoding="utf-8")
            project_cfg = ProjectConfig(path=tmp_dir, agents={})
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            store.load_project.return_value = project_cfg
            with (
                mock.patch("aicage.cli._remove_config.SettingsStore", return_value=store),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_project_config("codex")

        output = stdout.getvalue()
        self.assertIn("Agent config not found:", output)
        self.assertIn("codex", output)
        store.save_project.assert_not_called()

    def test_remove_project_config_agent_existing_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            config_path.write_text("agents: {codex: {}}", encoding="utf-8")
            project_cfg = ProjectConfig(path=tmp_dir, agents={"codex": AgentConfig(base="ubuntu")})
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            store.load_project.return_value = project_cfg
            with (
                mock.patch("aicage.cli._remove_config.SettingsStore", return_value=store),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_project_config("codex")

        output = stdout.getvalue()
        self.assertIn("Agent config removed:", output)
        self.assertIn("Project config updated:", output)
        store.save_project.assert_called_once()
        self.assertEqual({}, project_cfg.agents)
