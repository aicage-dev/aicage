from textual import work
from textual.app import ComposeResult

from ._textual_app import TextualApp
from .views.image_update_confirm_screen import ImageUpdateConfirmScreen


class ImageUpdateApp(TextualApp[bool | None]):
    def __init__(self, image_ref: str) -> None:
        super().__init__("container setup")
        self._image_ref = image_ref

    def compose(self) -> ComposeResult:
        if False:
            yield

    def on_mount(self) -> None:
        self._show_image_update_confirmation()

    @work(exclusive=True)
    async def _show_image_update_confirmation(self) -> None:
        await self._show_image_update_confirmation_impl()

    async def _show_image_update_confirmation_impl(self) -> None:
        result = await self.push_screen_wait(ImageUpdateConfirmScreen(self._image_ref))
        self.exit(bool(result))
