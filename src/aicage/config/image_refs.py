from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME


def local_image_ref(local_image_repository: str, agent: str, base: str) -> str:
    tag = f"{agent}-{base}".lower().replace("/", "-")
    return f"{local_image_repository}:{tag}"


def default_extended_image_ref(agent: str, base: str, extensions: list[str]) -> str:
    tag = "-".join([agent, base, *sorted(extensions)]).lower().replace("/", "-")
    return f"{DEFAULT_EXTENDED_IMAGE_NAME}:{tag}"


def extended_image_name(image_ref: str) -> str:
    _, _, tag = image_ref.rpartition(":")
    return tag or image_ref
