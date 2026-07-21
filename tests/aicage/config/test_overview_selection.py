from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config import overview_selection
from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig, ProjectConfig
from aicage.config.run_config_draft import create_run_config_draft
from aicage.registry.image_selection.interaction import (
    BaseChoiceRequest,
    ExtensionChoiceOption,
    MissingExtensionsRequest,
)


class OverviewSelectionTests(TestCase):
    def test_resolve_overview_selection_returns_base_image_ref_without_extensions(
        self,
    ) -> None:
        draft = create_run_config_draft(
            Path("/repo"),
            "codex",
            ProjectConfig(path="/repo", agents={"codex": AgentConfig(base="ubuntu")}),
            ParsedArgs(False, "", "codex", [], False, [], None),
        )
        context = ConfigContext(
            store=mock.Mock(),
            project_cfg=draft.project_cfg,
            agents={
                "codex": AgentMetadata(
                    agent_path_files=[],
                    agent_path_directories=[],
                    agent_full_name="Codex CLI",
                    agent_homepage="https://example.com",
                    build_local=False,
                    valid_bases={"ubuntu": "repo:ubuntu"},
                    local_definition_dir=Path("/test-tmp/agent"),
                )
            },
            bases={
                "ubuntu": BaseMetadata(
                    from_image="ubuntu:latest",
                    base_image_distro="Ubuntu",
                    base_image_description="Default",
                    architectures=["amd64", "arm64"],
                    build_local=False,
                    local_definition_dir=Path("/test-tmp/base"),
                )
            },
            extensions={},
        )

        with mock.patch(
            "aicage.config.overview_selection.base_image_ref",
            return_value="repo:ubuntu",
        ):
            selection = overview_selection.resolve_overview_selection(draft, context)

        self.assertEqual("ubuntu", selection.base)
        self.assertEqual("repo:ubuntu", selection.image_ref)

    def test_resolve_overview_selection_uses_sorted_extensions_for_default_image_ref(
        self,
    ) -> None:
        draft = create_run_config_draft(
            Path("/repo"),
            "codex",
            ProjectConfig(
                path="/repo",
                agents={
                    "codex": AgentConfig(base="ubuntu", extensions=["zeta", "alpha"])
                },
            ),
            ParsedArgs(False, "", "codex", [], False, [], None),
        )
        context = ConfigContext(
            store=mock.Mock(),
            project_cfg=draft.project_cfg,
            agents={
                "codex": AgentMetadata(
                    agent_path_files=[],
                    agent_path_directories=[],
                    agent_full_name="Codex CLI",
                    agent_homepage="https://example.com",
                    build_local=False,
                    valid_bases={"ubuntu": "repo:ubuntu"},
                    local_definition_dir=Path("/test-tmp/agent"),
                )
            },
            bases={
                "ubuntu": BaseMetadata(
                    from_image="ubuntu:latest",
                    base_image_distro="Ubuntu",
                    base_image_description="Default",
                    architectures=["amd64", "arm64"],
                    build_local=False,
                    local_definition_dir=Path("/test-tmp/base"),
                )
            },
            extensions={},
        )

        with (
            mock.patch(
                "aicage.config.overview_selection.ensure_extensions_exist",
                return_value=False,
            ),
            mock.patch("aicage.config.overview_selection.write_extended_image_config"),
            mock.patch(
                "aicage.config.overview_selection.base_image_ref",
                return_value="repo:ubuntu",
            ),
        ):
            selection = overview_selection.resolve_overview_selection(draft, context)

        self.assertEqual("aicage-extended:codex-ubuntu-alpha-zeta", selection.image_ref)


class OverviewSelectionInteractionTests(TestCase):
    def test_choose_base(self) -> None:
        with self.assertRaises(RuntimeError):
            overview_selection._OverviewSelectionInteraction().choose_base(
                BaseChoiceRequest(
                    agent="codex",
                    context=mock.Mock(),
                    agent_metadata=mock.Mock(),
                    default_base="ubuntu",
                )
            )

    def test_choose_extensions(self) -> None:
        with self.assertRaises(RuntimeError):
            overview_selection._OverviewSelectionInteraction().choose_extensions(
                [ExtensionChoiceOption(name="gh", description="GitHub CLI")]
            )

    def test_choose_image_ref(self) -> None:
        with self.assertRaises(RuntimeError):
            overview_selection._OverviewSelectionInteraction().choose_image_ref(
                "repo:tag"
            )

    def test_choose_missing_extensions(self) -> None:
        with self.assertRaises(RuntimeError):
            overview_selection._OverviewSelectionInteraction().choose_missing_extensions(
                MissingExtensionsRequest(
                    agent="codex",
                    missing=["gh"],
                    stored_image_ref="repo:tag",
                    project_config_path=Path("/repo/project.yml"),
                    other_projects=[],
                )
            )
