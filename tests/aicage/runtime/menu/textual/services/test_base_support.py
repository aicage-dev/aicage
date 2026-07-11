from unittest import TestCase

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.runtime.menu.textual.services import base_support

from .._test_support import _build_context, _build_draft


class BaseSupportTests(TestCase):
    def test_base_metadata_for_draft_returns_available_bases(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
        )

        options = base_support.base_metadata_for_draft(draft, _build_context())

        self.assertEqual(["alpine", "ubuntu"], sorted(options))

    def test_ensure_base_default_sets_default_base(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
        )

        base_support.ensure_base_default(draft, _build_context())
        self.assertEqual("ubuntu", draft.agent_cfg.base)
