import os

from aicage.constants import PROXY_ENV_NAMES
from aicage.runtime.run_args import EnvVar


def proxy_env_vars_from_host() -> list[EnvVar]:
    env_vars: list[EnvVar] = []
    for name in PROXY_ENV_NAMES:
        value = os.environ.get(name)
        if value:
            env_vars.append(EnvVar(name=name, value=value))
    return env_vars


def proxy_build_args_from_host() -> list[str]:
    args: list[str] = []
    for env_var in proxy_env_vars_from_host():
        args.extend(["--build-arg", f"{env_var.name}={env_var.value}"])
    return args


def proxy_run_env_args_from_host() -> list[str]:
    args: list[str] = []
    for env_var in proxy_env_vars_from_host():
        args.extend(["-e", f"{env_var.name}={env_var.value}"])
    return args
