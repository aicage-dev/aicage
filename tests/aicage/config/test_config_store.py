import hashlib
import tempfile
from pathlib import Path
from unittest import TestCase, mock

import yaml

from aicage.config.config_store import SettingsStore, _IndentedSafeDumper
from aicage.config.project_config import AgentConfig, _AgentMounts, _ProjectConfig


class ConfigStoreTests(TestCase):
    def test_increase_indent_indents_list_items(self) -> None:
        content = yaml.dump({"extensions": ["java17"]}, Dumper=_IndentedSafeDumper)

        self.assertEqual("extensions:\n  - java17\n", content)

    def test_project_config_path_returns_hashed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir)

            with mock.patch(
                "aicage.config.config_store.PROJECTS_DIR",
                projects_dir,
            ):
                store = SettingsStore()
                project_path = Path("/repo")
                expected = hashlib.sha256(str(project_path).encode("utf-8")).hexdigest()

                path = store.project_config_path(project_path)

            self.assertEqual(store.projects_dir / f"{expected}.yml", path)

    def test_global_config_path_returns_global_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            global_path = Path(tmp_dir) / "global.yml"
            with mock.patch(
                "aicage.config.config_store.GLOBAL_CONFIG_PATH", global_path
            ):
                path = SettingsStore().global_config_path()

        self.assertEqual(global_path, path)

    def test_tree_config_path_returns_hashed_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trees_dir = Path(tmp_dir) / "trees"
            with mock.patch("aicage.config.config_store.TREES_DIR", trees_dir):
                store = SettingsStore()
                path = store.tree_config_path(Path("/project"))

        expected = hashlib.sha256(str(Path("/project")).encode("utf-8")).hexdigest()
        self.assertEqual(trees_dir / f"{expected}.yml", path)

    def test_load_project_returns_empty_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir)

            with mock.patch(
                "aicage.config.config_store.PROJECTS_DIR",
                projects_dir,
            ):
                store = SettingsStore()
                project_path = projects_dir / "project"
                project_path.mkdir(parents=True, exist_ok=True)

                project_cfg = store.load_project(project_path)

            self.assertEqual(
                _ProjectConfig(path=str(project_path), agents={}), project_cfg
            )

    def test_save_project_writes_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir)

            with mock.patch(
                "aicage.config.config_store.PROJECTS_DIR",
                projects_dir,
            ):
                store = SettingsStore()
                project_path = projects_dir / "project"
                project_path.mkdir(parents=True, exist_ok=True)

                project_cfg = _ProjectConfig(path=str(project_path), agents={})
                project_cfg.agents["codex"] = AgentConfig(
                    base="fedora",
                    docker_args="--add-host=host.docker.internal:host-gateway",
                    mounts=_AgentMounts(),
                    extensions=["java17"],
                )
                store.save_project(project_path, project_cfg)

                config_path = store.project_config_path(project_path)
                with config_path.open("r", encoding="utf-8") as handle:
                    raw = yaml.safe_load(handle)
                content = config_path.read_text(encoding="utf-8")

            self.assertEqual(project_cfg.to_mapping(), raw)
            self.assertIn("    extensions:\n      - java17\n", content)

    def test_load_project_accepts_indentless_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir)

            with mock.patch(
                "aicage.config.config_store.PROJECTS_DIR",
                projects_dir,
            ):
                store = SettingsStore()
                project_path = projects_dir / "project"
                project_path.mkdir(parents=True, exist_ok=True)
                config_path = store.project_config_path(project_path)
                config_path.write_text(
                    "path: /project\nagents:\n  codex:\n    extensions:\n    - java17\n",
                    encoding="utf-8",
                )

                project_cfg = store.load_project(project_path)

            self.assertEqual(["java17"], project_cfg.agents["codex"].extensions)

    def test_load_global_returns_empty_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            global_path = Path(tmp_dir) / "global.yml"
            with mock.patch(
                "aicage.config.config_store.GLOBAL_CONFIG_PATH", global_path
            ):
                config = SettingsStore().load_global()

        self.assertEqual({}, config.agents)

    def test_save_global_writes_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            global_path = Path(tmp_dir) / "global.yml"
            config = _ProjectConfig(
                path="/", agents={"codex": AgentConfig(base="ubuntu")}
            )
            with mock.patch(
                "aicage.config.config_store.GLOBAL_CONFIG_PATH", global_path
            ):
                SettingsStore().save_global(config)

            self.assertEqual(
                config.to_mapping(), yaml.safe_load(global_path.read_text())
            )

    def test_save_global_writes_false_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            global_path = Path(tmp_dir) / "global.yml"
            config = _ProjectConfig(
                path="/",
                agents={
                    "codex": AgentConfig(
                        mounts=_AgentMounts(gitconfig=False, docker=True),
                        extension_mounts={"gh": False, "gcloud": True},
                    )
                },
            )
            with mock.patch(
                "aicage.config.config_store.GLOBAL_CONFIG_PATH", global_path
            ):
                SettingsStore().save_global(config)

            saved = yaml.safe_load(global_path.read_text())

        self.assertEqual(
            {
                "path": "/",
                "agents": {
                    "codex": {
                        "mounts": {"gitconfig": False, "docker": True},
                        "extension_mounts": {"gh": False, "gcloud": True},
                    }
                },
            },
            saved,
        )

    def test_load_tree_returns_empty_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trees_dir = Path(tmp_dir) / "trees"
            with mock.patch("aicage.config.config_store.TREES_DIR", trees_dir):
                config = SettingsStore().load_tree(Path("/project"))

        self.assertEqual({}, config.agents)

    def test_save_tree_writes_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            trees_dir = Path(tmp_dir) / "trees"
            config = _ProjectConfig(
                path="/project", agents={"codex": AgentConfig(base="ubuntu")}
            )
            with mock.patch("aicage.config.config_store.TREES_DIR", trees_dir):
                store = SettingsStore()
                store.save_tree(Path("/project"), config)
                saved = store.load_tree(Path("/project"))

        self.assertEqual(config, saved)
