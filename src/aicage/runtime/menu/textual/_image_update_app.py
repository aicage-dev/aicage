from textual import work
from textual.app import App, ComposeResult
from textual.content import Content

from aicage.config.resources import find_packaged_path

from .views.image_update_confirm_screen import ImageUpdateConfirmScreen


class ImageUpdateApp(App[bool | None]):
    CSS_PATH = find_packaged_path("textual/app.tcss")
    ENABLE_COMMAND_PALETTE = False
    INLINE_PADDING = 0

    def __init__(self, image_ref: str) -> None:
        super().__init__()
        self._image_ref = image_ref
        self.title = "aicage"
        self.sub_title = "container setup"

    def compose(self) -> ComposeResult:
        if False:
            yield

    def format_title(self, title: str, sub_title: str) -> Content:
        if not sub_title:
            return Content.from_markup(f"[b]{title}[/b]")
        return Content.from_markup(f"[b]{title}[/b] [dim]— {sub_title}[/dim]")

    def on_mount(self) -> None:
        self._show_image_update_confirmation()

    @work(exclusive=True)
    async def _show_image_update_confirmation(self) -> None:
        await self._show_image_update_confirmation_impl()

    async def _show_image_update_confirmation_impl(self) -> None:
        result = await self.push_screen_wait(ImageUpdateConfirmScreen(self._image_ref))
        self.exit(bool(result))
