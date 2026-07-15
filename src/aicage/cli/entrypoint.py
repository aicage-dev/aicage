import os
import subprocess
import sys
from collections.abc import Sequence

from aicage import __version__
from aicage._logging import get_logger
from aicage.cli._info_config import info_project_config
from aicage.cli._parse import parse_cli
from aicage.cli._remove_config import remove_project_config
from aicage.cli._version_check import maybe_prompt_update
from aicage.cli_types import ParsedArgs
from aicage.config.runtime_config import RunConfig, load_run_config
from aicage.docker.errors import DockerError
from aicage.docker.run import print_run_command, run_container
from aicage.errors import AicageError
from aicage.paths import GLOBAL_LOG_PATH
from aicage.registry.ensure_image import ensure_image
from aicage.runtime.menu.prompts.mode import set_assume_yes
from aicage.runtime.run_args import DockerRunArgs
from aicage.runtime.run_plan import build_run_args


def main(argv: Sequence[str] | None = None) -> int:
    parsed_argv: Sequence[str] = argv if argv is not None else sys.argv[1:]
    logger = get_logger()
    exit_code = 0
    try:
        parsed: ParsedArgs = parse_cli(parsed_argv)
        set_assume_yes(parsed.yes)
        if maybe_prompt_update(__version__):
            _restart_with_current_args(parsed_argv)
        if parsed.config_action == "info":
            info_project_config()
        elif parsed.config_action == "remove":
            remove_project_config(parsed.config_agent)
        else:
            run_config: RunConfig = load_run_config(parsed.agent, parsed)
            run_args: DockerRunArgs = build_run_args(config=run_config, parsed=parsed)
            logger.info("Resolved run config for agent %s", run_config.agent)
            ensure_image(run_config)

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
    os.execv(sys.executable, [sys.executable, "-m", "aicage", *parsed_argv])
