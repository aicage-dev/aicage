"""Credential-agent image resolution."""

from aicage.constants import CREDENTIAL_AGENT_IMAGE
from aicage.docker.errors import DockerError
from aicage.docker.query import get_local_image_id
from aicage.registry.ensure_util_image import ensure_util_image
from aicage.reporting import OperationReporter


def _credential_image(reporter: OperationReporter) -> tuple[str, str]:
    ensure_util_image(CREDENTIAL_AGENT_IMAGE, reporter)
    image_id = get_local_image_id(CREDENTIAL_AGENT_IMAGE)
    if image_id is None:
        raise DockerError(
            "Credential-agent image is unavailable after setup: "
            f"{CREDENTIAL_AGENT_IMAGE}."
        )
    return CREDENTIAL_AGENT_IMAGE, image_id
