import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.config import _inheritance as inheritance
from aicage.config.config_store import SettingsStore
from aicage.config.project_config import AgentConfig, _AgentMounts, _ProjectConfig


class InheritanceTests(TestCase):
    def test_load_effective_project_config_applies_scopes_from_global_to_project(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root_path = Path(tmp_dir)
            project_path = root_path / "workspace" / "team" / "project"
            outer_tree_path = project_path.parents[1]
            inner_tree_path = project_path.parent
            with (
                mock.patch(
                    "aicage.config.config_store.PROJECTS_DIR",
                    root_path / "projects",
                ),
                mock.patch("aicage.config.config_store.TREES_DIR", root_path / "trees"),
                mock.patch(
                    "aicage.config.config_store.GLOBAL_CONFIG_PATH",
                    root_path / "global.yml",
                ),
            ):
                store = SettingsStore()
                store.save_global(
                    _ProjectConfig(
                        path="/",
                        agents={
                            "codex": AgentConfig(
                                base="ubuntu",
                                docker_args="--global",
                                extensions=["global"],
                                shares=["global"],
                            )
                        },
                    )
                )
                store.save_tree(
                    outer_tree_path,
                    _ProjectConfig(
                        path=str(outer_tree_path),
                        agents={
                            "codex": AgentConfig(
                                docker_args="--outer-tree",
                                mounts=_AgentMounts(gitconfig=True),
                                extensions=["outer"],
                                shares=["outer"],
                            )
                        },
                    ),
                )
                store.save_tree(
                    inner_tree_path,
                    _ProjectConfig(
                        path=str(inner_tree_path),
                        agents={
                            "codex": AgentConfig(
                                docker_args="--inner-tree",
                                mounts=_AgentMounts(gitconfig=False),
                                extensions=["inner"],
                                shares=["inner"],
                            )
                        },
                    ),
                )
                store.save_tree(
                    project_path,
                    _ProjectConfig(
                        path=str(project_path),
                        agents={
                            "codex": AgentConfig(
                                docker_args="--project-tree",
                                extensions=["project-tree"],
                                shares=["project-tree"],
                            )
                        },
                    ),
                )
                config = inheritance.load_effective_project_config(
                    store,
                    project_path,
                    _ProjectConfig(
                        path=str(project_path),
                        agents={
                            "codex": AgentConfig(
                                docker_args="--project",
                                extensions=["project"],
                                shares=["project"],
                            )
                        },
                    ),
                )

        agent_config = config.agents["codex"]
        self.assertEqual("ubuntu", agent_config.base)
        self.assertEqual(
            "--global --outer-tree --inner-tree --project-tree --project",
            agent_config.docker_args,
        )
        self.assertFalse(agent_config.mounts.gitconfig)
        self.assertEqual(
            ["global", "outer", "inner", "project-tree", "project"],
            agent_config.extensions,
        )
        self.assertEqual(
            ["global", "outer", "inner", "project-tree", "project"],
            agent_config.shares,
        )

    def test_load_effective_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            with (
                mock.patch(
                    "aicage.config.config_store.PROJECTS_DIR",
                    Path(tmp_dir) / "projects",
                ),
                mock.patch(
                    "aicage.config.config_store.TREES_DIR", Path(tmp_dir) / "trees"
                ),
                mock.patch(
                    "aicage.config.config_store.GLOBAL_CONFIG_PATH",
                    Path(tmp_dir) / "global.yml",
                ),
            ):
                store = SettingsStore()
                project_path = Path(tmp_dir) / "workspace" / "project"
                store.save_global(
                    _ProjectConfig(
                        path="/", agents={"codex": AgentConfig(base="ubuntu")}
                    )
                )
                store.save_tree(
                    project_path.parent,
                    _ProjectConfig(
                        path=str(project_path.parent),
                        agents={"codex": AgentConfig(extensions=["gh"])},
                    ),
                )
                config = inheritance.load_effective_project_config(
                    store,
                    project_path,
                    _ProjectConfig(
                        path=str(project_path),
                        agents={"codex": AgentConfig(shares=["data"])},
                    ),
                )

        self.assertEqual("ubuntu", config.agents["codex"].base)
        self.assertEqual(["gh"], config.agents["codex"].extensions)
        self.assertEqual(["data"], config.agents["codex"].shares)

    def test_merge_project_configs(self) -> None:
        config = inheritance.merge_project_configs(
            [
                _ProjectConfig(
                    path="/",
                    agents={
                        "codex": AgentConfig(
                            base="ubuntu",
                            docker_args="--global",
                            extensions=["global"],
                            mounts=_AgentMounts(gitconfig=True),
                        )
                    },
                ),
                _ProjectConfig(
                    path="/project",
                    agents={
                        "codex": AgentConfig(
                            docker_args="--local",
                            extensions=["local"],
                            mounts=_AgentMounts(gitconfig=False),
                        )
                    },
                ),
            ],
            Path("/project"),
        )

        agent_config = config.agents["codex"]
        self.assertEqual("ubuntu", agent_config.base)
        self.assertEqual("--global --local", agent_config.docker_args)
        self.assertEqual(["global", "local"], agent_config.extensions)
        self.assertFalse(agent_config.mounts.gitconfig)

    def test_merge_agent_configs(self) -> None:
        config = inheritance.merge_agent_configs(
            AgentConfig(shares=["global"]), AgentConfig(shares=["local"])
        )

        self.assertEqual(["global", "local"], config.shares)

    def test_merge_agent_configs_deduplicates_extensions(self) -> None:
        config = inheritance.merge_agent_configs(
            AgentConfig(extensions=["gh"]), AgentConfig(extensions=["gh"])
        )

        self.assertEqual(["gh"], config.extensions)

    def test_merge_agent_configs_inherits_disabled_mounts(self) -> None:
        config = inheritance.merge_agent_configs(
            AgentConfig(mounts=_AgentMounts(gitconfig=False, docker=False)),
            AgentConfig(),
        )

        self.assertFalse(config.mounts.gitconfig)
        self.assertFalse(config.mounts.docker)

    def test_rebase_agent_config_preserves_effective_values_without_inheritance_duplicates(
        self,
    ) -> None:
        inherited = AgentConfig(
            base="ubuntu",
            docker_args="--global",
            extensions=["gh"],
            shares=["global"],
            mounts=_AgentMounts(gitconfig=True),
            extension_mounts={"gh": True},
        )
        effective = AgentConfig(
            base="ubuntu",
            docker_args="--global --local",
            extensions=["gh", "gcloud"],
            shares=["global", "local"],
            mounts=_AgentMounts(gitconfig=True, ssh=False),
            extension_mounts={"gh": True, "gcloud": True},
        )

        config = inheritance.rebase_agent_config(effective, inherited)

        self.assertIsNone(config.base)
        self.assertEqual("--local", config.docker_args)
        self.assertEqual(["gcloud"], config.extensions)
        self.assertEqual(["local"], config.shares)
        self.assertIsNone(config.mounts.gitconfig)
        self.assertFalse(config.mounts.ssh)
        self.assertEqual({"gcloud": True}, config.extension_mounts)
