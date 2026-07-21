from unittest import TestCase, mock

from aicage.runtime.menu.textual._models import ExtrasValues
from aicage.runtime.menu.textual.views import docker_args_screen


class ExtrasScreenTests(TestCase):
    def test_compose_builds_extras_widgets(self) -> None:
        screen = docker_args_screen.DockerArgsScreen(ExtrasValues(""))

        widgets = list(screen.compose())

        self.assertEqual(1, len(widgets))

    def test_action_accept_saves_selected_values(self) -> None:
        screen = docker_args_screen.DockerArgsScreen(ExtrasValues(""))

        def query_one_side_effect(selector: str, _expected_type: object) -> mock.Mock:
            widget = mock.Mock()
            if selector == "#docker_args":
                widget.text = "--rm\n--init"
            return widget

        with (
            mock.patch.object(screen, "query_one", side_effect=query_one_side_effect),
            mock.patch.object(screen, "dismiss") as dismiss_mock,
        ):
            screen.action_accept()

        dismiss_mock.assert_called_once_with(ExtrasValues("--rm\n--init"))

    def test_action_cancel_dismisses_none(self) -> None:
        screen = docker_args_screen.DockerArgsScreen(ExtrasValues(""))

        with mock.patch.object(screen, "dismiss") as dismiss_mock:
            screen.action_cancel()

        dismiss_mock.assert_called_once_with(None)

    def test_on_button_pressed_dispatches_ok(self) -> None:
        screen = docker_args_screen.DockerArgsScreen(ExtrasValues(""))
        event = mock.Mock()
        event.button.id = "ok"

        with mock.patch.object(screen, "action_accept") as accept_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        accept_mock.assert_called_once_with()

    def test_on_button_pressed_clear_empties_text_area(self) -> None:
        screen = docker_args_screen.DockerArgsScreen(ExtrasValues(""))
        event = mock.Mock()
        event.button.id = "clear"

        with mock.patch.object(screen, "_clear_docker_args") as clear_mock:
            screen.on_button_pressed(event)

        event.stop.assert_called_once_with()
        clear_mock.assert_called_once_with()

    def test_clear_docker_args_resets_text_area(self) -> None:
        screen = docker_args_screen.DockerArgsScreen(ExtrasValues(""))
        docker_args = mock.Mock()

        with mock.patch.object(screen, "query_one", return_value=docker_args):
            screen._clear_docker_args()

        docker_args.load_text.assert_called_once_with("")
