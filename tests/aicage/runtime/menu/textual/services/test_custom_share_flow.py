from unittest import TestCase

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.runtime.menu.textual._models import CustomShareValue, ShareEditorResult
from aicage.runtime.menu.textual._state import OverviewState
from aicage.runtime.menu.textual.services import custom_share_flow

from .._test_support import _build_draft


class CustomShareFlowTests(TestCase):
    def test_add_custom_share_adds_normalized_value(self) -> None:
        state = OverviewState(None, [], [], False)
        draft = _build_draft(
            AgentConfig(), ParsedArgs(False, "", "codex", [], False, [], None)
        )

        added = custom_share_flow.add_custom_share(state, draft, "/tmp/logs")

        self.assertTrue(added)
        self.assertEqual([CustomShareValue("/tmp/logs")], state.custom_shares)

    def test_update_custom_share_replaces_existing_value(self) -> None:
        state = OverviewState(None, [], [CustomShareValue("/tmp/logs")], False)
        draft = _build_draft(
            AgentConfig(), ParsedArgs(False, "", "codex", [], False, [], None)
        )

        updated = custom_share_flow.update_custom_share(
            state,
            draft,
            "/tmp/logs",
            ShareEditorResult("/tmp/cache", False),
        )

        self.assertTrue(updated)
        self.assertEqual([CustomShareValue("/tmp/cache")], state.custom_shares)
