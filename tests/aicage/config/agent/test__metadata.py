from pathlib import Path
from unittest import TestCase, mock

from aicage.config.agent._metadata import build_agent_metadata
from aicage.config.agent.models import (
    _AGENT_FULL_NAME_KEY,
    _AGENT_HOMEPAGE_KEY,
    _AGENT_PATH_DIRECTORIES_KEY,
    _AGENT_PATH_KEY,
    _BASE_EXCLUDE_KEY,
    _BUILD_LOCAL_KEY,
)
from aicage.config.base.models import BaseMetadata
from aicage.constants import IMAGE_REGISTRY, IMAGE_REPOSITORY


class AgentMetadataBuilderTests(TestCase):
    def test_build_agent_metadata_filters_bases_and_sets_refs(self) -> None:
        bases = {
            "ubuntu": BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/ubuntu"),
            ),
            "alpine": BaseMetadata(
                from_image="alpine:latest",
                base_image_distro="Alpine",
                base_image_description="Minimal",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/alpine"),
            ),
        }
        mapping = {
            _AGENT_PATH_KEY: {_AGENT_PATH_DIRECTORIES_KEY: ["~/.codex"]},
            _AGENT_FULL_NAME_KEY: "Codex",
            _AGENT_HOMEPAGE_KEY: "https://example.com",
            _BUILD_LOCAL_KEY: False,
            _BASE_EXCLUDE_KEY: ["alpine"],
        }

        metadata = build_agent_metadata(
            agent_name="codex",
            agent_mapping=mapping,
            bases=bases,
            definition_dir=Path("/test-tmp/agent"),
        )

        self.assertEqual(
            {"ubuntu": f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}:codex-ubuntu"},
            metadata.valid_bases,
        )

    def test_build_agent_metadata_excludes_bases_for_unsupported_host_architecture(
        self,
    ) -> None:
        bases = {
            "arch": BaseMetadata(
                from_image="archlinux:latest",
                base_image_distro="Arch Linux",
                base_image_description="Rolling",
                architectures=["amd64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/arch"),
            ),
            "ubuntu": BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path("/test-tmp/ubuntu"),
            ),
        }
        mapping = {
            _AGENT_FULL_NAME_KEY: "Codex",
            _AGENT_HOMEPAGE_KEY: "https://example.com",
            _BUILD_LOCAL_KEY: False,
        }

        with mock.patch(
            "aicage.config.base.architecture.platform.machine", return_value="aarch64"
        ):
            metadata = build_agent_metadata(
                agent_name="codex",
                agent_mapping=mapping,
                bases=bases,
                definition_dir=Path("/test-tmp/agent"),
            )

        self.assertEqual(
            {"ubuntu": f"{IMAGE_REGISTRY}/{IMAGE_REPOSITORY}:codex-ubuntu"},
            metadata.valid_bases,
        )
