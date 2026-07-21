from pathlib import Path
from unittest import TestCase, mock

from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.project_config import ProjectConfig
from aicage.config.run_config import RunConfig
from aicage.registry.image_selection.models import ImageSelection
from aicage.runtime.menu.textual import setup
from aicage.runtime.menu.textual.screens.execution_screen import ExecutionScreen


class PrepareImageWithTextualAppTests(TestCase):
    def test_prepare_image_with_textual_app_raises_app_error(self) -> None:
        run_config = _build_run_config()

        with mock.patch.object(
            setup._SetupApp,
            "run",
            return_value=RuntimeError("boom"),
        ):
            with self.assertRaises(RuntimeError):
                setup.prepare_image_with_textual_app(run_config)


class ComposeTests(TestCase):
    def test_compose_yields_execution_screen(self) -> None:
        app = setup._SetupApp(_build_run_config())

        widgets = list(app.compose())

        self.assertEqual(1, len(widgets))
        self.assertIsInstance(widgets[0], ExecutionScreen)


class OnMountTests(TestCase):
    def test_on_mount_starts_prepare(self) -> None:
        app = setup._SetupApp(_build_run_config())

        with mock.patch.object(app, "_prepare") as prepare_mock:
            app.on_mount()

        prepare_mock.assert_called_once_with()


def _build_run_config() -> RunConfig:
    project_path = Path("/test-tmp/project")
    return RunConfig(
        project_path=project_path,
        agent="codex",
        context=ConfigContext(
            store=mock.Mock(),
            project_cfg=ProjectConfig(path=str(project_path), agents={}),
            agents={
                "codex": AgentMetadata(
                    agent_path_files=[],
                    agent_path_directories=["~/.codex"],
                    agent_full_name="Codex CLI",
                    agent_homepage="https://example.com",
                    build_local=False,
                    valid_bases={"ubuntu": "ghcr.io/aicage/aicage:codex-ubuntu"},
                    local_definition_dir=Path("/test-tmp/agent"),
                )
            },
            bases={
                "ubuntu": BaseMetadata(
                    from_image="ubuntu:latest",
                    base_image_distro="Ubuntu",
                    base_image_description="Default",
                    architectures=["amd64", "arm64"],
                    build_local=False,
                    local_definition_dir=Path("/test-tmp/base"),
                )
            },
            extensions={},
        ),
        selection=ImageSelection(
            image_ref="ghcr.io/aicage/aicage:codex-ubuntu",
            base="ubuntu",
            extensions=[],
            base_image_ref="ghcr.io/aicage/aicage:codex-ubuntu",
        ),
        project_docker_args="",
        mounts=[],
        env=[],
    )
