from aicage._logging import get_logger
from aicage.docker.query import get_local_rootfs_layers


def base_layer_missing(base_image_ref: str, final_image_ref: str) -> bool:
    base_layers = get_local_rootfs_layers(base_image_ref)
    if base_layers is None:
        logger = get_logger()
        logger.warning(
            "Skipping base image layer validation for %s -> %s; missing local layer data.",
            base_image_ref,
            final_image_ref,
        )
        return False
    final_layers = get_local_rootfs_layers(final_image_ref)
    if final_layers is None:
        logger = get_logger()
        logger.warning(
            "Skipping base image layer validation for %s -> %s; missing local layer data.",
            base_image_ref,
            final_image_ref,
        )
        return False
    return base_layers[-1] not in final_layers
