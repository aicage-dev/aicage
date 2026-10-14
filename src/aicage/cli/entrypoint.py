import os
import subprocess  # nosec B404 -- subprocess types are used for structured Docker error handling.
import sys
from collections.abc import Sequence

from aicage import __version__
from aicage._logging import get_logger
from aicage.cli._info_config import info_project_config
from aicage.cli._parse import parse_cli
from aicage.cli._remove_config import remove_project_config
from aicage.cli._version_check import maybe_prompt_update
from aicage.cli_types import ParsedArgs
from aicage.config.runtime_config import (
    RunConfig,
    configure_inherited_config,
    load_run_config,
)
from aicage.docker.errors import DockerError
from aicage.docker.run import print_run_command, run_container
from aicage.errors import AicageError
from aicage.paths import GLOBAL_LOG_PATH
from aicage.runtime.image_setup import prepare_image
from aicage.runtime.menu.interaction import (
    RuntimeInteraction,
    create_runtime_interaction,
)
from aicage.runtime.run_args import DockerRunArgs
from aicage.runtime.run_plan import build_run_args


def main(argv: Sequence[str] | None = None) -> int:
    parsed_argv: Sequence[str] = argv if argv is not None else sys.argv[1:]
    logger = get_logger()
    exit_code = 0
    try:
        parsed: ParsedArgs = parse_cli(parsed_argv)
        interaction = create_runtime_interaction(parsed.menu)
        if maybe_prompt_update(__version__, interaction.confirm_aicage_update):
            _restart_with_current_args(parsed_argv)
        if _handle_config_action(parsed, interaction):
            pass
        else:
            run_config: RunConfig | None = load_run_config(
                parsed.agent, interaction, parsed
            )
            if run_config is None:
                return exit_code
            run_args: DockerRunArgs = build_run_args(config=run_config, parsed=parsed)
            logger.info("Resolved run config for agent %s", run_config.agent)
            prepare_image(run_config, interaction)

            if parsed.dry_run:
                print_run_command(run_args)
                logger.info("Dry-run docker command printed.")
            else:
                run_container(run_args)
    except KeyboardInterrupt:
        print()
        logger.warning("Interrupted by user.")
        exit_code = 130
    except DockerError as exc:
        _print_docker_error(exc)
        logger.error("CLI error: %s", exc)
        exit_code = 1
    except AicageError as exc:
        print(f"[aicage] {exc}", file=sys.stderr)
        logger.error("CLI error: %s", exc)
        exit_code = 1
    except Exception as exc:
        _print_unexpected_error(exc)
        logger.exception("Unhandled exception during CLI execution")
        exit_code = 1
    return exit_code


def _handle_config_action(
    parsed: ParsedArgs,
    interaction: RuntimeInteraction,
) -> bool:
    if parsed.config_action == "info":
        _info_config(parsed.config_scope)
        return True
    if parsed.config_action == "remove":
        _remove_config(parsed.config_agent, parsed.config_scope)
        return True
    if parsed.config_action in {"global", "tree"}:
        configure_inherited_config(
            parsed.config_action, parsed.config_agent or "", interaction, parsed
        )
        return True
    return False


def _info_config(scope: str | None) -> None:
    if scope is None:
        info_project_config()
    else:
        info_project_config(scope)


def _remove_config(agent: str | None, scope: str | None) -> None:
    if scope is None:
        remove_project_config(agent)
    else:
        remove_project_config(agent, scope)


def _print_docker_error(exc: DockerError) -> None:
    print(f"[aicage] {exc}", file=sys.stderr)
    cause = exc.__cause__
    if not isinstance(cause, subprocess.CalledProcessError):
        return
    stderr = cause.stderr
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    if stderr:
        print(stderr.rstrip(), file=sys.stderr)


def _print_unexpected_error(exc: Exception) -> None:
    print(f"[aicage] {_format_unexpected_error(exc)}", file=sys.stderr)
    print(f"[aicage] More details in log: {GLOBAL_LOG_PATH}", file=sys.stderr)


def _format_unexpected_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return exc.__class__.__name__
    return f"{exc.__class__.__name__}: {message}"


def _restart_with_current_args(parsed_argv: Sequence[str]) -> None:
    os.execv(  # nosec B606 -- restart re-executes the current Python interpreter with current CLI args.
        sys.executable, [sys.executable, "-m", "aicage", *parsed_argv]
    )
