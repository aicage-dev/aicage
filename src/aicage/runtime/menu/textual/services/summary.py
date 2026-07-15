from aicage.config.context import ConfigContext
from aicage.config.run_config_draft import RunConfigDraft

from .._models import ExtrasValues, SharesValues
from ._share_support import built_in_share_values


def shares_values(draft: RunConfigDraft, context: ConfigContext) -> SharesValues:
    return SharesValues(
        shares=list(draft.agent_cfg.shares),
        built_in_shares=built_in_share_values(draft, context.extensions),
    )


def extras_values(draft: RunConfigDraft) -> ExtrasValues:
    return ExtrasValues(
        docker_args=draft.agent_cfg.docker_args,
    )


def extensions_summary(selected_extensions: list[str]) -> str:
    if not selected_extensions:
        return "none"
    if len(selected_extensions) == 1:
        return "1 selected"
    return f"{len(selected_extensions)} selected"


def _list_summary(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _shares_summary(values: SharesValues) -> str:
    parts: list[str] = []
    if values.shares:
        parts.append(_list_summary(values.shares))
    built_in_labels = [
        item.label.lower() for item in values.built_in_shares if item.enabled
    ]
    if built_in_labels:
        parts.append(", ".join(built_in_labels))
    if not parts:
        return "none"
    return ", ".join(parts)


def extras_summary(values: ExtrasValues) -> str:
    return "yes" if values.docker_args else "none"
