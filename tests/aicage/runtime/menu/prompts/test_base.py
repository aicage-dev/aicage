from pathlib import Path
from unittest import TestCase, mock

from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.project_config import ProjectConfig
from aicage.runtime._errors import RuntimeExecutionError
from aicage.runtime.menu.prompts.base import (
    BaseSelectionRequest,
    _available_bases,
    _base_options,
    prompt_for_base,
)


class PromptTests(TestCase):
    def test_prompt_for_base_validates_choice(self) -> None:
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch("builtins.input", return_value="fedora"),
        ):
            with self.assertRaises(RuntimeExecutionError):
                prompt_for_base(
                    BaseSelectionRequest(
                        agent="codex",
                        context=self._build_context(["ubuntu"]),
                        agent_metadata=self._agent_metadata(["ubuntu"]),
                    )
                )

    def test_prompt_for_base_accepts_number_and_default(self) -> None:
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch(
                "aicage.runtime.menu.prompts.base.resolve_default_base",
                return_value="ubuntu",
            ),
            mock.patch("builtins.input", side_effect=["2", ""]),
        ):
            choice = prompt_for_base(
                BaseSelectionRequest(
                    agent="codex",
                    context=self._build_context(["alpine", "ubuntu"]),
                    agent_metadata=self._agent_metadata(["alpine", "ubuntu"]),
                )
            )
            self.assertEqual("ubuntu", choice)
            default_choice = prompt_for_base(
                BaseSelectionRequest(
                    agent="codex",
                    context=self._build_context(["ubuntu"]),
                    agent_metadata=self._agent_metadata(["ubuntu"]),
                )
            )
            self.assertEqual("ubuntu", default_choice)
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch("builtins.input", return_value="3"),
        ):
            with self.assertRaises(RuntimeExecutionError):
                prompt_for_base(
                    BaseSelectionRequest(
                        agent="codex",
                        context=self._build_context(["alpine", "ubuntu"]),
                        agent_metadata=self._agent_metadata(["alpine", "ubuntu"]),
                    )
                )

    def test_prompt_for_base_uses_host_default_on_enter(self) -> None:
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch(
                "aicage.runtime.menu.prompts.base.resolve_default_base",
                return_value="fedora",
            ),
            mock.patch("builtins.input", return_value=""),
        ):
            choice = prompt_for_base(
                BaseSelectionRequest(
                    agent="codex",
                    context=self._build_context(["fedora", "ubuntu"]),
                    agent_metadata=self._agent_metadata(["fedora", "ubuntu"]),
                )
            )
        self.assertEqual("fedora", choice)

    def test_prompt_for_base_accepts_default_without_list(self) -> None:
        with (
            mock.patch("sys.stdin.isatty", return_value=True),
            mock.patch("builtins.input", return_value=""),
        ):
            choice = prompt_for_base(
                BaseSelectionRequest(
                    agent="codex",
                    context=self._build_context([]),
                    agent_metadata=self._agent_metadata([]),
                )
            )
        self.assertEqual("ubuntu", choice)

    def test_base_options_returns_descriptions(self) -> None:
        context = self._build_context(["ubuntu"])
        options = _base_options(context, self._agent_metadata(["ubuntu"]))
        self.assertEqual(
            [("ubuntu", "Default")],
            [(option.base, option.description) for option in options],
        )

    def test_base_options_filters_excluded_bases(self) -> None:
        context = self._build_context(["alpine", "ubuntu"])
        options = _base_options(
            context,
            self._agent_metadata(["alpine", "ubuntu"], base_exclude=["alpine"]),
        )
        self.assertEqual(
            [("ubuntu", "Default")],
            [(option.base, option.description) for option in options],
        )

    def test_available_bases_returns_list(self) -> None:
        context = self._build_context(["ubuntu", "alpine"])
        options = _base_options(context, self._agent_metadata(["ubuntu", "alpine"]))
        self.assertEqual(["alpine", "ubuntu"], _available_bases(options))

    @staticmethod
    def _build_context(bases: list[str]) -> ConfigContext:
        base_entries = PromptTests._bases_with_names(bases)
        agents = PromptTests._agents_with_bases(bases)
        return ConfigContext(
            store=mock.Mock(),
            project_cfg=ProjectConfig(path="/test-tmp/project", agents={}),
            agents=agents,
            bases=base_entries,
            extensions={},
        )

    @staticmethod
    def _agent_metadata(
        bases: list[str],
        base_exclude: list[str] | None = None,
        base_distro_exclude: list[str] | None = None,
    ) -> AgentMetadata:
        return AgentMetadata(
            agent_path_files=[],
            agent_path_directories=["~/.codex"],
            agent_full_name="Codex CLI",
            agent_homepage="https://example.com",
            build_local=False,
            valid_bases={name: f"repo:{name}" for name in bases},
            local_definition_dir=Path("/test-tmp/codex"),
            base_exclude=base_exclude or [],
            base_distro_exclude=base_distro_exclude or [],
        )

    @staticmethod
    def _bases_with_names(bases: list[str]) -> dict[str, BaseMetadata]:
        return {
            name: BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                architectures=["amd64", "arm64"],
                build_local=False,
                local_definition_dir=Path(f"/test-tmp/{name}"),
            )
            for name in bases
        }

    @staticmethod
    def _agents_with_bases(bases: list[str]) -> dict[str, AgentMetadata]:
        return {
            "codex": AgentMetadata(
                agent_path_files=[],
                agent_path_directories=["~/.codex"],
                agent_full_name="Codex CLI",
                agent_homepage="https://example.com",
                build_local=False,
                valid_bases={name: f"repo:{name}" for name in bases},
                local_definition_dir=Path("/test-tmp/codex"),
            )
        }
