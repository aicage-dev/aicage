from pathlib import Path
from unittest import TestCase, mock

from aicage.config.agent.models import AgentMetadata
from aicage.config.base.models import BaseMetadata
from aicage.config.context import ConfigContext
from aicage.config.project_config import ProjectConfig
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME
from aicage.runtime._errors import RuntimeExecutionError
from aicage.runtime.prompts.base import base_options
from aicage.runtime.prompts.image_choice import (
    ExtendedImageOption,
    ImageChoiceRequest,
    _build_image_options,
    _parse_image_choice_response,
    _render_image_prompt,
    prompt_for_image_choice,
)


class PromptImageChoiceTests(TestCase):
    def test_prompt_for_image_choice_defaults_to_base(self) -> None:
        context = self._context()
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        with (
            mock.patch("aicage.runtime.prompts.image_choice.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value=""),
        ):
            choice = prompt_for_image_choice(request)
        self.assertEqual("base", choice.kind)
        self.assertEqual("ubuntu", choice.value)

    def test_prompt_for_image_choice_accepts_extended_by_number(self) -> None:
        context = self._context()
        extended = [
            ExtendedImageOption(
                name="custom",
                base="ubuntu",
                description="Custom",
                extensions=["ext"],
                image_ref=f"{DEFAULT_EXTENDED_IMAGE_NAME}:custom",
            )
        ]
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=extended,
        )
        with (
            mock.patch("aicage.runtime.prompts.image_choice.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="2"),
        ):
            choice = prompt_for_image_choice(request)
        self.assertEqual("extended", choice.kind)
        self.assertEqual("custom", choice.value)

    def test_prompt_for_image_choice_rejects_invalid(self) -> None:
        context = self._context()
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        with (
            mock.patch("aicage.runtime.prompts.image_choice.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="fedora"),
        ):
            with self.assertRaises(RuntimeExecutionError):
                prompt_for_image_choice(request)

    def test_prompt_for_image_choice_uses_default_when_assume_yes(self) -> None:
        context = self._context()
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        with (
            mock.patch("aicage.runtime.prompts.image_choice.assume_yes_enabled", return_value=True),
            mock.patch("aicage.runtime.prompts.image_choice.resolve_default_base", return_value="ubuntu"),
            mock.patch("aicage.runtime.prompts.image_choice.ensure_tty_for_prompt") as tty_mock,
            mock.patch("builtins.input") as input_mock,
        ):
            choice = prompt_for_image_choice(request)
        self.assertEqual("base", choice.kind)
        self.assertEqual("ubuntu", choice.value)
        tty_mock.assert_not_called()
        input_mock.assert_not_called()

    def test_render_image_prompt_uses_default_when_no_options(self) -> None:
        request = ImageChoiceRequest(
            agent="codex",
            context=self._context(),
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        prompt = _render_image_prompt(request, [], "ubuntu")
        self.assertEqual("Select image for 'codex' (runtime to use inside the container): [ubuntu]: ", prompt)

    def test_parse_image_choice_accepts_base_name(self) -> None:
        context = self._context()
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        bases = base_options(context, request.agent_metadata)
        options = _build_image_options(bases, [])
        choice = _parse_image_choice_response("ubuntu", bases, [], options, "ubuntu")
        self.assertEqual("base", choice.kind)
        self.assertEqual("ubuntu", choice.value)

    def test_parse_image_choice_accepts_extended_name(self) -> None:
        context = self._context()
        extended = [
            ExtendedImageOption(
                name="custom",
                base="ubuntu",
                description="Custom",
                extensions=["ext"],
                image_ref=f"{DEFAULT_EXTENDED_IMAGE_NAME}:custom",
            )
        ]
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=extended,
        )
        bases = base_options(context, request.agent_metadata)
        options = _build_image_options(bases, extended)
        choice = _parse_image_choice_response("custom", bases, extended, options, "ubuntu")
        self.assertEqual("extended", choice.kind)
        self.assertEqual("custom", choice.value)

    def test_parse_image_choice_rejects_invalid_number(self) -> None:
        context = self._context()
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        bases = base_options(context, request.agent_metadata)
        options = _build_image_options(bases, [])
        with self.assertRaises(RuntimeExecutionError):
            _parse_image_choice_response("99", bases, [], options, "ubuntu")

    def test_parse_image_choice_uses_resolved_default_on_empty(self) -> None:
        context = self._context()
        request = ImageChoiceRequest(
            agent="codex",
            context=context,
            agent_metadata=self._agent_metadata(),
            extended_options=[],
        )
        bases = base_options(context, request.agent_metadata)
        options = _build_image_options(bases, [])
        choice = _parse_image_choice_response("", bases, [], options, "fedora")
        self.assertEqual("base", choice.kind)
        self.assertEqual("fedora", choice.value)

    @staticmethod
    def _context() -> ConfigContext:
        bases = {
            "ubuntu": BaseMetadata(
                from_image="ubuntu:latest",
                base_image_distro="Ubuntu",
                base_image_description="Default",
                build_local=False,
                local_definition_dir=Path("/tmp/ubuntu"),
            )
        }
        return ConfigContext(
            store=mock.Mock(),
            project_cfg=ProjectConfig(path="/tmp/project", agents={}),
            agents={},
            bases=bases,
            extensions={},
        )

    @staticmethod
    def _agent_metadata() -> AgentMetadata:
        return AgentMetadata(
            agent_path_files=[],
            agent_path_directories=["~/.codex"],
            agent_full_name="Codex",
            agent_homepage="https://example.com",
            build_local=True,
            valid_bases={"ubuntu": "ghcr.io/aicage/aicage:codex-ubuntu"},
            local_definition_dir=Path("/tmp/def"),
        )
