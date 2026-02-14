from pathlib import Path
from typing import Any

from aicage.config._schema_validation import load_schema, validate_schema_mapping
from aicage.config._yaml import expect_bool, expect_string
from aicage.config.agent.models import (
    AGENT_PATH_DIRECTORIES_KEY,
    AGENT_PATH_FILES_KEY,
    AGENT_PATH_KEY,
    BUILD_LOCAL_KEY,
)
from aicage.config.errors import ConfigError

_AGENT_SCHEMA_PATH = "validation/agent.schema.json"
_AGENT_CONTEXT = "agent metadata"


def validate_agent_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
    schema = load_schema(_AGENT_SCHEMA_PATH)
    return validate_schema_mapping(
        mapping,
        schema,
        _AGENT_CONTEXT,
        normalizer=_apply_defaults,
        value_validator=_validate_value,
    )


def ensure_required_files(agent_name: str, agent_dir: Path) -> None:
    missing = [name for name in ("install.sh", "version.sh") if not (agent_dir / name).is_file()]
    if missing:
        raise ConfigError(f"Agent '{agent_name}' is missing {', '.join(missing)}.")


def _apply_defaults(mapping: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(mapping)
    normalized.setdefault(BUILD_LOCAL_KEY, True)
    agent_path = normalized.get(AGENT_PATH_KEY)
    if isinstance(agent_path, dict):
        agent_path = dict(agent_path)
        agent_path.setdefault(AGENT_PATH_FILES_KEY, [])
        agent_path.setdefault(AGENT_PATH_DIRECTORIES_KEY, [])
        normalized[AGENT_PATH_KEY] = agent_path
    return normalized


def _validate_value(value: Any, schema_entry: dict[str, Any], context: str) -> None:
    schema_type = schema_entry.get("type")
    if schema_type == "string":
        expect_string(value, context)
        return
    if schema_type == "boolean":
        expect_bool(value, context)
        return
    if schema_type == "array":
        _expect_str_list(value, context, schema_entry)
        return
    if schema_type == "object":
        _expect_mapping(value, context, schema_entry)
        return
    raise ConfigError(f"{context} has unsupported schema type '{schema_type}'.")


def _expect_str_list(value: Any, context: str, schema_entry: dict[str, Any]) -> None:
    if not isinstance(value, list):
        raise ConfigError(f"{context} must be a list.")
    item_schema = schema_entry.get("items", {})
    item_type = item_schema.get("type")
    if item_type != "string":
        raise ConfigError(f"{context} items must be strings.")
    for item in value:
        expect_string(item, context)


def _expect_mapping(value: Any, context: str, schema_entry: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ConfigError(f"{context} must be a mapping.")
    validate_schema_mapping(
        value,
        schema_entry,
        context,
        value_validator=_validate_value,
    )
