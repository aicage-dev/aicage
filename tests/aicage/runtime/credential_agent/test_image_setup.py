from pathlib import Path
from unittest import TestCase, mock

from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, _ProjectConfig
from aicage.config.run_config import RunConfig
from aicage.registry.image_selection.models import ImageSelection
from aicage.runtime.credential_agent import image_setup


def _run_config() -> RunConfig:
    return RunConfig(
        project_path=Path("/test-tmp/project"),
        agent="codex",
        context=ConfigContext(
            store=mock.Mock(),
            project_cfg=_ProjectConfig(path="/test-tmp/project", agents={}),
            agents={"codex": mock.create_autospec(AgentMetadata, instance=True)},
            bases={"ubuntu": mock.create_autospec(BaseMetadata, instance=True)},
            extensions={},
        ),
        selection=ImageSelection("repo:tag", "ubuntu", [], "repo:tag"),
        project_docker_args="",
        mounts=[],
        env=[],
    )


class CredentialImageSetupTests(TestCase):
    def test_prepare_credential_image_skips_when_credentials_are_disabled(self) -> None:
        run_config = _run_config()
        interaction = mock.Mock()

        with mock.patch.object(image_setup, "util_image_setup_action") as plan_mock:
            image_setup.prepare_credential_image(run_config, interaction)

        plan_mock.assert_not_called()
        interaction.execute_operation.assert_not_called()

    def test_prepare_credential_image_skips_a_current_image(self) -> None:
        run_config = _run_config()
        run_config.context.project_cfg.agents["codex"] = AgentConfig.from_mapping(
            {"mounts": {"ssh": True}}
        )
        interaction = mock.Mock()

        with mock.patch.object(
            image_setup,
            "util_image_setup_action",
            return_value=image_setup.UtilImageSetupAction.SKIP,
        ):
            image_setup.prepare_credential_image(run_config, interaction)

        interaction.execute_operation.assert_not_called()

    def test_prepare_credential_image_executes_required_setup(self) -> None:
        run_config = _run_config()
        run_config.context.project_cfg.agents["codex"] = AgentConfig.from_mapping(
            {"mounts": {"gnupg": True}}
        )
        interaction = mock.Mock()
        reporter = mock.Mock()
        interaction.execute_operation.side_effect = lambda operation: operation(reporter)

        with (
            mock.patch.object(
                image_setup,
                "util_image_setup_action",
                return_value=image_setup.UtilImageSetupAction.SETUP,
            ),
            mock.patch.object(image_setup, "ensure_util_image") as ensure_mock,
        ):
            image_setup.prepare_credential_image(run_config, interaction)

        ensure_mock.assert_called_once_with(
            image_setup.CREDENTIAL_AGENT_IMAGE,
            reporter,
            setup_action=image_setup.UtilImageSetupAction.SETUP,
        )
