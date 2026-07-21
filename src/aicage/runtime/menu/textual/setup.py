from collections.abc import Callable

from aicage.docker.reporting import OperationReporter

from ._app import OverviewApp

_ImageSetupOperation = Callable[[OperationReporter], None]


def confirm_image_update_with_textual_app(image_ref: str) -> bool:
    return bool(OverviewApp.for_image_update_confirmation(image_ref).run(inline=True))


def execute_image_setup_with_textual_app(operation: _ImageSetupOperation) -> None:
    result = OverviewApp.for_execution(operation).run(inline=True)
    if isinstance(result, BaseException):
        raise result
