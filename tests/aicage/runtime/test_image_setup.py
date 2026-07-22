from unittest import TestCase, mock

from aicage.registry.ensure_image import ImageSetupPlan
from aicage.runtime import image_setup


class PrepareImageTests(TestCase):
    def test_prepare_image_skips_execution_when_setup_not_needed(self) -> None:
        run_config = mock.Mock()
        interaction = mock.Mock()

        with (
            mock.patch(
                "aicage.runtime.image_setup.image_setup_plan",
                return_value=ImageSetupPlan(needs_setup=False),
            ),
        ):
            image_setup.prepare_image(run_config, interaction)

        interaction.execute_image_setup.assert_not_called()

    def test_prepare_image_runs_execution_when_setup_is_needed(self) -> None:
        run_config = mock.Mock()
        interaction = mock.Mock()

        with (
            mock.patch(
                "aicage.runtime.image_setup.image_setup_plan",
                return_value=ImageSetupPlan(needs_setup=True),
            ),
        ):
            image_setup.prepare_image(run_config, interaction)

        interaction.execute_image_setup.assert_called_once()

    def test_prepare_image_confirms_update_through_interaction(self) -> None:
        run_config = mock.Mock()
        run_config.selection.base_image_ref = "repo:tag"
        interaction = mock.Mock(confirm_image_update=mock.Mock(return_value=True))
        reporter = mock.Mock()

        with (
            mock.patch(
                "aicage.runtime.image_setup.image_setup_plan",
                return_value=ImageSetupPlan(
                    needs_setup=True,
                    needs_update_confirmation=True,
                ),
            ),
            mock.patch("aicage.runtime.image_setup.ensure_image") as ensure_image_mock,
        ):
            interaction.execute_image_setup.side_effect = lambda operation: operation(
                reporter
            )
            image_setup.prepare_image(run_config, interaction)

        interaction.confirm_image_update.assert_called_once_with("repo:tag")
        ensure_image_mock.assert_called_once_with(
            run_config,
            update_approved=True,
            reporter=reporter,
        )

    def test_prepare_image_passes_rejected_update_to_ensure_image(self) -> None:
        run_config = mock.Mock()
        run_config.selection.base_image_ref = "repo:tag"
        interaction = mock.Mock(confirm_image_update=mock.Mock(return_value=False))
        reporter = mock.Mock()

        with (
            mock.patch(
                "aicage.runtime.image_setup.image_setup_plan",
                return_value=ImageSetupPlan(
                    needs_setup=True,
                    needs_update_confirmation=True,
                ),
            ),
            mock.patch("aicage.runtime.image_setup.ensure_image") as ensure_image_mock,
        ):
            interaction.execute_image_setup.side_effect = lambda operation: operation(
                reporter
            )
            image_setup.prepare_image(run_config, interaction)

        interaction.confirm_image_update.assert_called_once_with("repo:tag")
        ensure_image_mock.assert_called_once_with(
            run_config,
            update_approved=False,
            reporter=reporter,
        )

    def test_prepare_image_skips_execution_when_only_confirmation_declined(
        self,
    ) -> None:
        run_config = mock.Mock()
        run_config.selection.base_image_ref = "repo:tag"
        interaction = mock.Mock(confirm_image_update=mock.Mock(return_value=False))

        with (
            mock.patch(
                "aicage.runtime.image_setup.image_setup_plan",
                return_value=ImageSetupPlan(
                    needs_setup=False,
                    needs_update_confirmation=True,
                ),
            ),
            mock.patch("aicage.runtime.image_setup.ensure_image") as ensure_image_mock,
        ):
            interaction.execute_image_setup.side_effect = lambda operation: operation(
                mock.Mock()
            )
            image_setup.prepare_image(run_config, interaction)

        interaction.confirm_image_update.assert_called_once_with("repo:tag")
        ensure_image_mock.assert_not_called()
