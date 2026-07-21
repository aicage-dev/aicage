from unittest import TestCase, mock

from textual.app import ComposeResult

from aicage.runtime.menu.textual import _textual_app


class _TestApp(_textual_app.TextualApp[object | None]):
    def compose(self) -> ComposeResult:
        if False:
            yield


class TextualAppTests(TestCase):
    def test_init_sets_title_and_subtitle(self) -> None:
        app = _TestApp("container setup")

        self.assertEqual("aicage", app.title)
        self.assertEqual("container setup", app.sub_title)

    def test_format_title_bolds_app_name_and_dims_subtitle(self) -> None:
        app = _TestApp("container setup")

        title = app.format_title("aicage", "container setup")

        self.assertEqual("aicage — container setup", str(title))

    def test_action_cancel_exits_none(self) -> None:
        app = _TestApp("container setup")

        with mock.patch.object(app, "exit") as exit_mock:
            app.action_cancel()

        exit_mock.assert_called_once_with(None)
