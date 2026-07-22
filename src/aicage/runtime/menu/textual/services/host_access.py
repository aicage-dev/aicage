from aicage.config.run_config_draft import RunConfigDraft

from .._ids import built_in_identity, built_in_selection_key, docker_selection_key
from .._models import (
    BuiltInShareValue,
    CustomShareValue,
    DockerOptionValue,
    HostAccessConfirmValues,
)


def built_in_selection_value(item: BuiltInShareValue) -> str:
    return built_in_selection_key(item.source, item.row_key or item.key)


def current_built_in_shares(
    selected: set[str],
    built_in_shares: list[BuiltInShareValue],
) -> list[BuiltInShareValue]:
    enabled_groups = {
        built_in_identity(item.source, item.key)
        for item in built_in_shares
        if built_in_selection_value(item) in selected
    }
    return [
        BuiltInShareValue(
            source=item.source,
            key=item.key,
            label=item.label,
            path=item.path,
            persisted=item.persisted,
            enabled=built_in_identity(item.source, item.key) in enabled_groups,
            row_key=item.row_key,
        )
        for item in built_in_shares
    ]


def built_in_group_selection_values(
    selection_value: str, built_in_shares: list[BuiltInShareValue]
) -> list[str]:
    selected_item = next(
        (
            item
            for item in built_in_shares
            if built_in_selection_value(item) == selection_value
        ),
        None,
    )
    if selected_item is None or selected_item.source != "extension":
        return []
    group_identity = built_in_identity(selected_item.source, selected_item.key)
    return [
        built_in_selection_value(item)
        for item in built_in_shares
        if built_in_identity(item.source, item.key) == group_identity
    ]


def current_docker_option(
    selected: set[str], persisted: bool | None
) -> DockerOptionValue:
    return DockerOptionValue(
        key="docker",
        label="Docker socket",
        persisted=persisted,
        enabled=docker_selection_key("socket") in selected,
    )


def _build_confirmation_request(
    built_in_shares: list[BuiltInShareValue],
    docker_option: DockerOptionValue,
) -> HostAccessConfirmValues:
    return HostAccessConfirmValues(
        docker_options=[
            docker_option
            for _ in [0]
            if docker_option.enabled and docker_option.persisted is not True
        ],
        git_support_shares=[
            item
            for item in built_in_shares
            if item.source == "git_support"
            and item.enabled
            and item.persisted is not True
        ],
        extension_shares=[
            item
            for item in built_in_shares
            if item.source == "extension"
            and item.enabled
            and item.persisted is not True
        ],
    )


def _merge_confirmed_host_access(
    built_in_shares: list[BuiltInShareValue],
    docker_option: DockerOptionValue,
    confirmed: HostAccessConfirmValues,
) -> tuple[list[BuiltInShareValue], DockerOptionValue]:
    confirmed_by_key = {
        built_in_identity(item.source, item.key): item.enabled
        for item in [*confirmed.git_support_shares, *confirmed.extension_shares]
    }
    merged_shares = [
        (
            BuiltInShareValue(
                source=item.source,
                key=item.key,
                label=item.label,
                path=item.path,
                persisted=item.persisted,
                enabled=confirmed_by_key.get(
                    built_in_identity(item.source, item.key), item.enabled
                ),
                row_key=item.row_key,
            )
            if built_in_identity(item.source, item.key) in confirmed_by_key
            else item
        )
        for item in built_in_shares
    ]
    confirmed_docker_by_key = {
        item.key: item.enabled for item in confirmed.docker_options
    }
    if "docker" not in confirmed_docker_by_key:
        return merged_shares, docker_option
    return (
        merged_shares,
        DockerOptionValue(
            key=docker_option.key,
            label=docker_option.label,
            persisted=docker_option.persisted,
            enabled=confirmed_docker_by_key["docker"],
        ),
    )


def _apply_confirmed_host_access(
    draft: RunConfigDraft,
    built_in_shares: list[BuiltInShareValue],
    custom_shares: list[CustomShareValue],
    docker_option: DockerOptionValue,
) -> None:
    draft.agent_cfg.shares = [item.value for item in custom_shares]
    for item in built_in_shares:
        if item.source == "git_support":
            setattr(draft.agent_cfg.mounts, item.key, item.enabled)
        elif item.source == "extension":
            draft.agent_cfg.extension_mounts[item.key] = item.enabled
    draft.agent_cfg.mounts.docker = docker_option.enabled
