from pathlib import Path
from unittest import mock

from aicage.cli_types import ParsedArgs
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.extensions.loader import ExtensionMetadata
from aicage.config.project_config import AgentConfig, ProjectConfig
from aicage.config.run_config_draft import create_run_config_draft


def _build_draft(
    agent_cfg: AgentConfig,
    parsed: ParsedArgs,
    project_path: Path = Path("/test-tmp/project"),
):
    return create_run_config_draft(
        project_path,
        "codex",
        ProjectConfig(path=str(project_path), agents={"codex": agent_cfg}),
        parsed,
    )


def _build_context() -> ConfigContext:
    return ConfigContext(
        store=mock.Mock(),
        project_cfg=ProjectConfig(path="/test-tmp/project", agents={}),
        agents={
            "codex": AgentMetadata(
                agent_path_files=[],
                agent_path_directories=["~/.codex"],
                agent_full_name="Codex CLI",
                agent_homepage="https://example.com",
                build_local=False,
                valid_bases={
                    "alpine": "repo:alpine",
                    "ubuntu": "repo:ubuntu",
                },
                local_definition_dir=Path("/test-tmp/codex"),
            )
        },
        bases={
            "alpine": BaseMetadata(
                from_image="alpine:latest",
                base_image_distro="Alpine",
                base_image_description="Minimal",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/alpine"),
            ),
            "ubuntu": BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/ubuntu"),
            ),
        },
        extensions={
            "gh": ExtensionMetadata(
                extension_id="gh",
                name="GitHub CLI",
                description="GitHub CLI",
                shares=["~/.config/gh"],
                directory=Path("/test-tmp/extensions/gh"),
                scripts_dir=Path("/test-tmp/extensions/gh/scripts"),
                dockerfile_path=None,
            ),
            "gcloud": ExtensionMetadata(
                extension_id="gcloud",
                name="Google Cloud CLI",
                description="Google Cloud CLI",
                shares=["~/.config/gcloud", "~/.boto"],
                directory=Path("/test-tmp/extensions/gcloud"),
                scripts_dir=Path("/test-tmp/extensions/gcloud/scripts"),
                dockerfile_path=None,
            ),
        },
    )
