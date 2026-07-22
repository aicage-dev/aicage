from collections.abc import Callable
from dataclasses import dataclass

from aicage.docker.reporting import OperationReporter
from aicage.registry.image_selection.models import ImageSelection

ImageSetupOperation = Callable[[OperationReporter | None], None]


@dataclass(frozen=True)
class _ConfigSelectionResult:
    selection: ImageSelection
    project_docker_args: str
