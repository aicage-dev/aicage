from collections.abc import Awaitable, Callable

from aicage.config.run_config_draft import RunConfigDraft

from .._models import (
    BuiltInShareValue,
    CustomShareValue,
    DockerOptionValue,
    HostAccessConfirmValues,
)
from .host_access import (
    _apply_confirmed_host_access,
    _build_confirmation_request,
    _merge_confirmed_host_access,
)


async def confirm_and_apply_host_access(
    draft: RunConfigDraft,
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
    docker_option: DockerOptionValue,
    confirm_host_access: Callable[
        [HostAccessConfirmValues], Awaitable[HostAccessConfirmValues | None]
    ],
) -> tuple[bool, list[BuiltInShareValue]]:
    confirmation_request = _build_confirmation_request(built_in_shares, docker_option)
    if (
        confirmation_request.docker_options
        or confirmation_request.git_support_shares
        or confirmation_request.extension_shares
    ):
        confirmed = await confirm_host_access(confirmation_request)
        if confirmed is None:
            return False, built_in_shares
        built_in_shares, docker_option = _merge_confirmed_host_access(
            built_in_shares, docker_option, confirmed
        )
    _apply_confirmed_host_access(draft, built_in_shares, custom_shares, docker_option)
    return True, built_in_shares
