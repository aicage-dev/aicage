import asyncio
from unittest import TestCase, mock

from aicage.runtime.menu.textual import _image_update_app


class ImageUpdateAppTests(TestCase):
    def test_compose_builds_no_root_widgets(self) -> None:
        app = _image_update_app.ImageUpdateApp("repo:tag")

        widgets = list(app.compose())

        self.assertEqual([], widgets)

    def test_init_sets_container_setup_subtitle(self) -> None:
        app = _image_update_app.ImageUpdateApp("repo:tag")

        self.assertEqual("container setup", app.sub_title)

    def test_format_title_bolds_app_name_and_dims_subtitle(self) -> None:
        app = _image_update_app.ImageUpdateApp("repo:tag")

        title = app.format_title("aicage", "container setup")

        self.assertEqual("aicage — container setup", str(title))

    def test_on_mount_starts_confirmation(self) -> None:
        app = _image_update_app.ImageUpdateApp("repo:tag")

        with mock.patch.object(app, "_show_image_update_confirmation") as show_mock:
            app.on_mount()

        show_mock.assert_called_once_with()

    def test_action_cancel_exits_none(self) -> None:
        app = _image_update_app.ImageUpdateApp("repo:tag")

        with mock.patch.object(app, "exit") as exit_mock:
            app.action_cancel()

        exit_mock.assert_called_once_with(None)

    def test_show_image_update_confirmation_exits_bool_result(self) -> None:
        app = _image_update_app.ImageUpdateApp("repo:tag")

        with (
            mock.patch.object(
                app, "push_screen_wait", new=mock.AsyncMock(return_value=True)
            ),
            mock.patch.object(app, "exit") as exit_mock,
        ):
            asyncio.run(app._show_image_update_confirmation_impl())

        exit_mock.assert_called_once_with(True)
