from unittest import TestCase, mock

from aicage.runtime.menu.textual import _app, setup
from aicage.runtime.menu.textual.screens.execution_screen import ExecutionScreen


class ConfirmImageUpdateWithTextualAppTests(TestCase):
    def test_confirm_image_update_with_textual_app_returns_false_for_none(self) -> None:
        app_mock = mock.Mock()
        app_mock.run.return_value = None

        with mock.patch(
            "aicage.runtime.menu.textual.setup.OverviewApp.for_image_update_confirmation",
            return_value=app_mock,
        ):
            self.assertFalse(setup.confirm_image_update_with_textual_app("repo:tag"))


class ExecuteImageSetupWithTextualAppTests(TestCase):
    def test_execute_image_setup_with_textual_app_raises_app_error(self) -> None:
        operation = mock.Mock()
        app_mock = mock.Mock()
        app_mock.run.return_value = RuntimeError("boom")

        with mock.patch(
            "aicage.runtime.menu.textual.setup.OverviewApp.for_execution",
            return_value=app_mock,
        ):
            with self.assertRaises(RuntimeError):
                setup.execute_image_setup_with_textual_app(operation)


class ComposeTests(TestCase):
    def test_compose_yields_execution_screen(self) -> None:
        app = _app.OverviewApp.for_execution(mock.Mock())

        widgets = list(app.compose())

        self.assertEqual(1, len(widgets))
        self.assertIsInstance(widgets[0], ExecutionScreen)


class OnMountTests(TestCase):
    def test_on_mount_starts_confirmation(self) -> None:
        app = _app.OverviewApp.for_image_update_confirmation("repo:tag")

        with mock.patch.object(
            app,
            "_show_image_update_confirmation",
        ) as show_confirmation_mock:
            app.on_mount()

        show_confirmation_mock.assert_called_once_with()

    def test_on_mount_starts_execution(self) -> None:
        app = _app.OverviewApp.for_execution(mock.Mock())

        with mock.patch.object(app, "_run_execution") as execute_mock:
            app.on_mount()

        execute_mock.assert_called_once_with()
