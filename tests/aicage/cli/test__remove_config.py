import io
import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli import _remove_config as remove_config
from aicage.config.project_config import AgentConfig, _ProjectConfig


class RemoveConfigTests(TestCase):
    def test_remove_agent_config_missing_project_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            with (
                mock.patch(
                    "aicage.cli._remove_config.SettingsStore", return_value=store
                ),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_agent_config("codex")

        output = stdout.getvalue()
        self.assertIn("Project config not found:", output)
        self.assertIn(str(config_path), output)

    def test_remove_agent_config_missing_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            config_path.write_text("agents: {}", encoding="utf-8")
            project_cfg = _ProjectConfig(path=tmp_dir, agents={})
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            store.load_project.return_value = project_cfg
            with (
                mock.patch(
                    "aicage.cli._remove_config.SettingsStore", return_value=store
                ),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_agent_config("codex")

        output = stdout.getvalue()
        self.assertIn("Agent config not found:", output)
        self.assertIn("codex", output)
        store.save_project.assert_not_called()

    def test_remove_agent_config_existing_entry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "project.yml"
            config_path.write_text("agents: {codex: {}}", encoding="utf-8")
            project_cfg = _ProjectConfig(
                path=tmp_dir, agents={"codex": AgentConfig(base="ubuntu")}
            )
            store = mock.Mock()
            store.project_config_path.return_value = config_path
            store.load_project.return_value = project_cfg
            with (
                mock.patch(
                    "aicage.cli._remove_config.SettingsStore", return_value=store
                ),
                mock.patch("sys.stdout", new_callable=io.StringIO) as stdout,
            ):
                remove_config.remove_agent_config("codex")

        output = stdout.getvalue()
        self.assertIn("Agent config removed:", output)
        self.assertIn("Project config updated:", output)
        store.save_project.assert_called_once()
        self.assertEqual({}, project_cfg.agents)

    def test_remove_agent_config_global(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "global.yml"
            config_path.touch()
            config = _ProjectConfig(path="/", agents={"codex": AgentConfig()})
            store = mock.Mock()
            store.global_config_path.return_value = config_path
            store.load_global.return_value = config
            with (
                mock.patch(
                    "aicage.cli._remove_config.SettingsStore", return_value=store
                ),
                mock.patch("sys.stdout", new_callable=io.StringIO),
            ):
                remove_config.remove_agent_config("codex", "global")

        store.save_global.assert_called_once_with(config)
        self.assertEqual({}, config.agents)

    def test_remove_agent_config_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "tree.yml"
            config_path.touch()
            config = _ProjectConfig(path="/test", agents={"codex": AgentConfig()})
            store = mock.Mock()
            store.tree_config_path.return_value = config_path
            store.load_tree.return_value = config
            with (
                mock.patch(
                    "aicage.cli._remove_config.SettingsStore", return_value=store
                ),
                mock.patch("sys.stdout", new_callable=io.StringIO),
            ):
                remove_config.remove_agent_config("codex", "tree")

        store.save_tree.assert_called_once()
        self.assertEqual({}, config.agents)
