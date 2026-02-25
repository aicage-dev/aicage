from dataclasses import dataclass

from aicage._logging import get_logger
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.filter import filter_bases
from aicage.config.context import ConfigContext
from aicage.runtime._errors import RuntimeExecutionError

from ._default_base import resolve_default_base
from ._tty import ensure_tty_for_prompt
from .mode import assume_yes_enabled


@dataclass(frozen=True)
class BaseSelectionRequest:
    agent: str
    context: ConfigContext
    agent_metadata: AgentMetadata


@dataclass(frozen=True)
class BaseOption:
    base: str
    description: str


def prompt_for_base(request: BaseSelectionRequest) -> str:
    bases = base_options(request.context, request.agent_metadata)
    default_base = resolve_default_base(available_bases(bases))
    if assume_yes_enabled():
        get_logger().info("Selected base '%s' for agent '%s' (assume-yes)", default_base, request.agent)
        return default_base
    ensure_tty_for_prompt()
    logger = get_logger()
    title = f"Select base image for '{request.agent}' (runtime to use inside the container):"

    if bases:
        print(title)
        for idx, option in enumerate(bases, start=1):
            suffix = " (default)" if option.base == default_base else ""
            print(f"  {idx}) {option.base}: {option.description}{suffix}")
        prompt = f"Enter number or name [{default_base}]: "
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

    if bases and choice not in available_bases(bases):
        options = ", ".join(available_bases(bases))
        raise RuntimeExecutionError(f"Invalid base '{choice}'. Valid options: {options}")
    logger.info("Selected base '%s' for agent '%s'", choice, request.agent)
    return choice


def base_options(context: ConfigContext, agent_metadata: AgentMetadata) -> list[BaseOption]:
    bases = filter_bases(context, agent_metadata)
    return [
        BaseOption(
            base=base,
            description=context.bases[base].base_image_description,
        )
        for base in sorted(bases)
    ]


def available_bases(options: list[BaseOption]) -> list[str]:
    return [option.base for option in options]
