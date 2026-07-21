import tempfile
from pathlib import Path, PurePosixPath
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.config_store import SettingsStore
from aicage.config.project_config import AgentConfig, _AgentMounts
from aicage.config.run_config_draft import RunConfigDraft
from aicage.config.runtime_config import RunConfig, load_run_config
from aicage.registry.errors import RegistryError
from aicage.registry.image_selection.models import ImageSelection
from aicage.runtime.run_args import EnvVar, MountSpec


class RuntimeConfigTests(TestCase):
    def test_load_run_config_reads_docker_args_and_mount_prefs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir)
            project_path = projects_dir / "project"
            project_path.mkdir()

            store = SettingsStore()

            project_cfg = store.load_project(project_path)
            project_cfg.agents["codex"] = AgentConfig(
                base="ubuntu",
                docker_args="--project",
                mounts=_AgentMounts(gitconfig=True),
            )
            store.save_project(project_path, project_cfg)

            def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                return SettingsStore()

            mounts = [
                MountSpec(
                    host_path=Path("/test-tmp/host"),
                    container_path=PurePosixPath("/test-tmp/container"),
                )
            ]
            env: list[EnvVar] = []
            with (
                mock.patch(
                    "aicage.config.runtime_config.SettingsStore", new=store_factory
                ),
                mock.patch(
                    "aicage.config.runtime_config.Path.cwd", return_value=project_path
                ),
                mock.patch(
                    "aicage.config.runtime_config.resolve_docker_args",
                    return_value=(mounts, env),
                ),
                mock.patch("aicage.config.runtime_config.apply_mount_preferences"),
                mock.patch(
                    "aicage.config.runtime_config.load_extensions", return_value={}
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_bases",
                    return_value=self._get_bases(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_agents",
                    return_value=self._get_agents(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.select_agent_image",
                    return_value=ImageSelection(
                        image_ref="ref",
                        base="ubuntu",
                        extensions=[],
                        base_image_ref="ref",
                    ),
                ),
            ):
                run_config = load_run_config("codex")

        self.assertIsInstance(run_config, RunConfig)
        self.assertEqual("--project", run_config.project_docker_args)
        self.assertEqual(mounts, run_config.mounts)
        self.assertEqual(env, run_config.env)

    def test_load_run_config_persists_new_docker_args(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            store = SettingsStore()
            project_cfg = store.load_project(project_path)
            project_cfg.agents["codex"] = AgentConfig(
                base="ubuntu",
                docker_args="--existing",
            )
            store.save_project(project_path, project_cfg)

            def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                return SettingsStore()

            parsed = ParsedArgs(
                dry_run=False,
                docker_args="--new",
                agent="codex",
                agent_args=[],
                docker_socket=False,
                shares=[],
                config_action=None,
                menu="none",
            )
            with (
                mock.patch(
                    "aicage.config.runtime_config.SettingsStore", new=store_factory
                ),
                mock.patch(
                    "aicage.config.runtime_config.Path.cwd", return_value=project_path
                ),
                mock.patch(
                    "aicage.config.runtime_config.resolve_docker_args",
                    return_value=([], []),
                ),
                mock.patch("aicage.config.runtime_config.apply_mount_preferences"),
                mock.patch(
                    "aicage.config.runtime_config.load_extensions", return_value={}
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_bases",
                    return_value=self._get_bases(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_agents",
                    return_value=self._get_agents(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.select_agent_image",
                    return_value=ImageSelection(
                        image_ref="ref",
                        base="ubuntu",
                        extensions=[],
                        base_image_ref="ref",
                    ),
                ),
                mock.patch(
                    "aicage.config.runtime_config.prompt_persist_docker_args",
                    return_value=True,
                ),
            ):
                run_config = load_run_config("codex", parsed)

        self.assertEqual("--existing", run_config.project_docker_args)

    def test_load_run_config_defaults_base_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            store = SettingsStore()
            project_cfg = store.load_project(project_path)
            project_cfg.agents["codex"] = AgentConfig()
            store.save_project(project_path, project_cfg)

            def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                return SettingsStore()

            with (
                mock.patch(
                    "aicage.config.runtime_config.SettingsStore", new=store_factory
                ),
                mock.patch(
                    "aicage.config.runtime_config.Path.cwd", return_value=project_path
                ),
                mock.patch(
                    "aicage.config.runtime_config.resolve_docker_args",
                    return_value=([], []),
                ),
                mock.patch("aicage.config.runtime_config.apply_mount_preferences"),
                mock.patch(
                    "aicage.config.runtime_config.load_extensions", return_value={}
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_bases",
                    return_value=self._get_bases(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_agents",
                    return_value=self._get_agents(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.select_agent_image",
                    return_value=ImageSelection(
                        image_ref="ref",
                        base="ubuntu",
                        extensions=[],
                        base_image_ref="ref",
                    ),
                ),
            ):
                run_config = load_run_config("codex")

        self.assertEqual("ubuntu", run_config.selection.base)

    def test_load_run_config_persists_share_mounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir) / "configs"
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            with mock.patch("aicage.config.config_store.PROJECTS_DIR", projects_dir):
                store = SettingsStore()
                project_cfg = store.load_project(project_path)
                project_cfg.agents["codex"] = AgentConfig(base="ubuntu")
                store.save_project(project_path, project_cfg)

                def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                    return SettingsStore()

                parsed = ParsedArgs(
                    dry_run=False,
                    docker_args="",
                    agent="codex",
                    agent_args=[],
                    docker_socket=False,
                    shares=["data", "logs:ro"],
                    config_action=None,
                    menu="none",
                )
                with (
                    mock.patch(
                        "aicage.config.runtime_config.SettingsStore", new=store_factory
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.Path.cwd",
                        return_value=project_path,
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.resolve_docker_args",
                        return_value=([], []),
                    ),
                    mock.patch("aicage.config.runtime_config.apply_mount_preferences"),
                    mock.patch(
                        "aicage.config.runtime_config.load_extensions", return_value={}
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.load_bases",
                        return_value=self._get_bases(),
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.load_agents",
                        return_value=self._get_agents(),
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.select_agent_image",
                        return_value=ImageSelection(
                            image_ref="ref",
                            base="ubuntu",
                            extensions=[],
                            base_image_ref="ref",
                        ),
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.prompt_persist_shares",
                        return_value=True,
                    ),
                ):
                    load_run_config("codex", parsed)

                updated_cfg = store.load_project(project_path)

        expected_data = str(project_path / "data")
        expected_logs = f"{project_path / 'logs'}:ro"
        self.assertEqual(
            [expected_data, expected_logs], updated_cfg.agents["codex"].shares
        )
        self.assertEqual([expected_data, expected_logs], parsed.shares)

    def test_load_run_config_merges_share_mounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            projects_dir = Path(tmp_dir) / "configs"
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            with mock.patch("aicage.config.config_store.PROJECTS_DIR", projects_dir):
                store = SettingsStore()
                project_cfg = store.load_project(project_path)
                project_cfg.agents["codex"] = AgentConfig(
                    base="ubuntu",
                    shares=[
                        str(project_path / "existing"),
                        f"{project_path / 'shared'}:ro",
                    ],
                )
                store.save_project(project_path, project_cfg)

                def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                    return SettingsStore()

                parsed = ParsedArgs(
                    dry_run=False,
                    docker_args="",
                    agent="codex",
                    agent_args=[],
                    docker_socket=False,
                    shares=["shared", "new"],
                    config_action=None,
                    menu="none",
                )
                prompt_mock = mock.Mock(return_value=True)
                with (
                    mock.patch(
                        "aicage.config.runtime_config.SettingsStore", new=store_factory
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.Path.cwd",
                        return_value=project_path,
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.resolve_docker_args",
                        return_value=([], []),
                    ),
                    mock.patch("aicage.config.runtime_config.apply_mount_preferences"),
                    mock.patch(
                        "aicage.config.runtime_config.load_extensions", return_value={}
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.load_bases",
                        return_value=self._get_bases(),
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.load_agents",
                        return_value=self._get_agents(),
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.select_agent_image",
                        return_value=ImageSelection(
                            image_ref="ref",
                            base="ubuntu",
                            extensions=[],
                            base_image_ref="ref",
                        ),
                    ),
                    mock.patch(
                        "aicage.config.runtime_config.prompt_persist_shares",
                        prompt_mock,
                    ),
                ):
                    load_run_config("codex", parsed)

                updated_cfg = store.load_project(project_path)

        expected_shared = str(project_path / "shared")
        expected_new = str(project_path / "new")
        expected_existing = str(project_path / "existing")
        self.assertEqual(
            [expected_shared, expected_new, expected_existing], parsed.shares
        )
        self.assertEqual(
            [expected_existing, f"{expected_shared}:ro", expected_new],
            updated_cfg.agents["codex"].shares,
        )
        prompt_mock.assert_called_once_with(
            [expected_new], [expected_existing, f"{expected_shared}:ro"]
        )

    def test_load_run_config_interactive_uses_overview_values_for_current_run(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            store = SettingsStore()
            project_cfg = store.load_project(project_path)
            project_cfg.agents["codex"] = AgentConfig(
                base="ubuntu",
                docker_args="--existing",
            )
            store.save_project(project_path, project_cfg)

            def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                return SettingsStore()

            parsed = ParsedArgs(
                dry_run=False,
                docker_args="--new",
                agent="codex",
                agent_args=[],
                docker_socket=True,
                shares=["logs"],
                config_action=None,
            )

            def overview_side_effect(
                draft: RunConfigDraft,
                _context: object,
                **_kwargs: object,
            ) -> tuple[ImageSelection, str]:
                draft.prefill_for_overview()
                draft.consume_overview_prefill()
                return (
                    ImageSelection(
                        image_ref="ref",
                        base="ubuntu",
                        extensions=[],
                        base_image_ref="ref",
                    ),
                    "--new",
                )

            with (
                mock.patch(
                    "aicage.config.runtime_config.SettingsStore", new=store_factory
                ),
                mock.patch(
                    "aicage.config.runtime_config.Path.cwd", return_value=project_path
                ),
                mock.patch(
                    "aicage.config.runtime_config.resolve_docker_args",
                    return_value=([], []),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_extensions", return_value={}
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_bases",
                    return_value=self._get_bases(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_agents",
                    return_value=self._get_agents(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.edit_draft_with_textual_app",
                    side_effect=overview_side_effect,
                ),
            ):
                run_config = load_run_config("codex", parsed)

        self.assertEqual("--new", run_config.project_docker_args)
        self.assertEqual("", parsed.docker_args)
        self.assertEqual([], parsed.shares)
        self.assertFalse(parsed.docker_socket)

    def test_load_run_config_applies_mount_preferences_before_runtime_resolution(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                return SettingsStore()

            parsed = ParsedArgs(
                dry_run=False,
                docker_args="",
                agent="codex",
                agent_args=[],
                docker_socket=False,
                shares=[],
                config_action=None,
                menu="none",
            )
            apply_mount_preferences_mock = mock.Mock()
            with (
                mock.patch(
                    "aicage.config.runtime_config.SettingsStore", new=store_factory
                ),
                mock.patch(
                    "aicage.config.runtime_config.Path.cwd", return_value=project_path
                ),
                mock.patch(
                    "aicage.config.runtime_config.resolve_docker_args",
                    return_value=([], []),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_extensions", return_value={}
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_bases",
                    return_value=self._get_bases(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_agents",
                    return_value=self._get_agents(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.select_agent_image",
                    return_value=ImageSelection(
                        image_ref="ref",
                        base="ubuntu",
                        extensions=[],
                        base_image_ref="ref",
                    ),
                ),
                mock.patch(
                    "aicage.config.runtime_config.apply_mount_preferences",
                    apply_mount_preferences_mock,
                ),
            ):
                load_run_config("codex", parsed)

        apply_mount_preferences_mock.assert_called_once()

    def test_load_run_config_rejects_unknown_config_agent_before_overview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_path = Path(tmp_dir) / "project"
            project_path.mkdir()

            def store_factory(*_args: object, **_kwargs: object) -> SettingsStore:
                return SettingsStore()

            parsed = ParsedArgs(
                dry_run=False,
                docker_args="",
                agent="config",
                agent_args=[],
                docker_socket=False,
                shares=[],
                config_action=None,
                menu="textual",
            )
            with (
                mock.patch(
                    "aicage.config.runtime_config.SettingsStore", new=store_factory
                ),
                mock.patch(
                    "aicage.config.runtime_config.Path.cwd", return_value=project_path
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_extensions", return_value={}
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_bases",
                    return_value=self._get_bases(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.load_agents",
                    return_value=self._get_agents(),
                ),
                mock.patch(
                    "aicage.config.runtime_config.edit_draft_with_textual_app"
                ) as overview_mock,
            ):
                with self.assertRaises(RegistryError) as raised:
                    load_run_config("config", parsed)

        self.assertEqual(
            (
                "Unknown agent 'config'. Use '--config' for config commands. "
                "Available agents: codex."
            ),
            str(raised.exception),
        )
        overview_mock.assert_not_called()

    @staticmethod
    def _get_bases() -> dict[str, BaseMetadata]:
        return {
            "ubuntu": BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/base"),
            )
        }

    @staticmethod
    def _get_agents() -> dict[str, AgentMetadata]:
        return {
            "codex": AgentMetadata(
                agent_path_files=[],
                agent_path_directories=["~/.codex"],
                agent_full_name="Codex CLI",
                agent_homepage="https://example.com",
                build_local=False,
                valid_bases={"ubuntu": "ghcr.io/aicage/aicage:codex-ubuntu"},
                local_definition_dir=Path("/test-tmp/agent"),
            )
        }
