from dataclasses import dataclass

from aicage._logging import get_logger
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.filter import filter_bases
from aicage.config.context import ConfigContext
from aicage.runtime._errors import RuntimeExecutionError
from aicage.runtime.menu.default_base import resolve_default_base

from ._tty import ensure_tty_for_prompt
from .mode import non_interactive_defaults_enabled


@dataclass(frozen=True)
class BaseSelectionRequest:
    agent: str
    context: ConfigContext
    agent_metadata: AgentMetadata
    default_base: str | None = None


@dataclass(frozen=True)
class _BaseOption:
    base: str
    description: str


def prompt_for_base(request: BaseSelectionRequest) -> str:
    bases = _base_options(request.context, request.agent_metadata)
    default_base = request.default_base or resolve_default_base(_available_bases(bases))
    if non_interactive_defaults_enabled():
        get_logger().info(
            "Selected base '%s' for agent '%s' (non-interactive defaults)",
            default_base,
            request.agent,
        )
        return default_base
    ensure_tty_for_prompt()
    logger = get_logger()
    title = f"Select base image for '{request.agent}' (runtime to use inside the container):"

    if bases:
        print(title)
        for idx, option in enumerate(bases, start=1):
            suffix = " (default)" if option.base == default_base else ""
            print(f"  {idx}) {option.base}: {option.description}{suffix}")
        prompt = f"Enter number or name (press Enter for default) [{default_base}]: "
    else:
        prompt = f"{title} [{default_base}]: "

    response = input(prompt).strip()
    if not response:
        choice = default_base
    elif response.isdigit() and bases:
        idx = int(response)
        if idx < 1 or idx > len(bases):
            raise RuntimeExecutionError(
                f"Invalid choice '{response}'. Pick a number between 1 and {len(bases)}."
            )
        choice = bases[idx - 1].base
    else:
        choice = response

    if bases and choice not in _available_bases(bases):
        options = ", ".join(_available_bases(bases))
        raise RuntimeExecutionError(f"Invalid base '{choice}'. Valid options: {options}")
    logger.info("Selected base '%s' for agent '%s'", choice, request.agent)
    return choice


def _base_options(context: ConfigContext, agent_metadata: AgentMetadata) -> list[_BaseOption]:
    bases = filter_bases(context, agent_metadata)
    return [
        _BaseOption(
            base=base,
            description=context.bases[base].base_image_description,
        )
        for base in sorted(bases)
    ]


def _available_bases(options: list[_BaseOption]) -> list[str]:
    return [option.base for option in options]
