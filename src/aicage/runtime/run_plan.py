from aicage._proxy import proxy_env_vars_from_host
from aicage.cli_types import ParsedArgs
from aicage.config.runtime_config import RunConfig
from aicage.runtime.run_args import DockerRunArgs, merge_docker_args


def build_run_args(config: RunConfig, parsed: ParsedArgs) -> DockerRunArgs:
    merged_docker_args: str = merge_docker_args(
        config.project_docker_args,
        parsed.docker_args,
    )
    return DockerRunArgs(
        image_ref=config.selection.image_ref,
        merged_docker_args=merged_docker_args,
        agent_args=parsed.agent_args,
        env=[*config.env, *proxy_env_vars_from_host()],
        mounts=list(config.mounts),
    )
