from unittest import IsolatedAsyncioTestCase, TestCase, mock

from textual.widgets import Button, SelectionList

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.runtime.menu.textual._models import BuiltInShareValue, CustomShareValue
from aicage.runtime.menu.textual._state import OverviewState
from aicage.runtime.menu.textual.overview.view import Overview

from .._test_support import _build_context, _build_draft


class OverviewTests(TestCase):
    def test_compose_builds_widgets(self) -> None:
        widgets = list(
            Overview(
                "codex", "/test-tmp/project", OverviewState(None, [], [], False)
            ).compose()
        )

        self.assertEqual(1, len(widgets))

    def test_compose_includes_project_path_row(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )

        self.assertEqual("/test-tmp/project", overview._project_path)

    def test_compose_formats_agent_and_project_context(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )

        self.assertEqual("codex", overview._agent)
        self.assertEqual("/test-tmp/project", overview._project_path)
        self.assertEqual("Agent:   codex", overview._context_line("Agent:", "codex"))
        self.assertEqual(
            "Project: /test-tmp/project",
            overview._context_line("Project:", "/test-tmp/project"),
        )

    def test_on_button_pressed_posts_accept_message(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        overview.post_message = mock.Mock()
        event = mock.Mock()
        event.button.id = "ok"

        overview.on_button_pressed(event)

        self.assertIsInstance(
            overview.post_message.call_args.args[0], Overview.AcceptRequested
        )

    def test_on_selection_list_selected_changed_updates_built_in_shares(self) -> None:
        state = OverviewState(
            None,
            [
                BuiltInShareValue(
                    "git_support", "ssh", "SSH", "/test-tmp/.ssh", None, True
                )
            ],
            [],
            False,
        )
        overview = Overview("codex", "/test-tmp/project", state)
        event = mock.Mock()
        event.selection_list.id = "shares_overview_list"
        event.selection_list.selected = []

        overview.on_selection_list_selected_changed(event)

        self.assertFalse(state.built_in_shares[0].enabled)

    def test_on_selection_list_selection_toggled_posts_custom_share_message(
        self,
    ) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        overview.post_message = mock.Mock()
        event = mock.Mock()
        event.selection_list.id = "shares_overview_list"
        event.selection.value = "custom:/test-tmp/logs"

        overview.on_selection_list_selection_toggled(event)

        event.selection_list.select.assert_called_once_with("custom:/test-tmp/logs")
        self.assertIsInstance(
            overview.post_message.call_args.args[0], Overview.EditCustomShareRequested
        )

    def test_on_selection_list_selection_toggled_syncs_extension_group_rows(
        self,
    ) -> None:
        overview = Overview(
            "codex",
            "/test-tmp/project",
            OverviewState(
                None,
                [
                    BuiltInShareValue(
                        "extension",
                        "gcloud",
                        "Extension gcloud",
                        "/test-tmp/gcloud",
                        None,
                        True,
                        "gcloud:/test-tmp/gcloud",
                    ),
                    BuiltInShareValue(
                        "extension",
                        "gcloud",
                        "Extension gcloud",
                        "/test-tmp/boto",
                        None,
                        True,
                        "gcloud:/test-tmp/boto",
                    ),
                ],
                [],
                False,
            ),
        )
        event = mock.Mock()
        event.selection_list.id = "shares_overview_list"
        event.selection.value = "builtin:extension:gcloud:/test-tmp/gcloud"
        event.selection_list.selected = ["builtin:extension:gcloud:/test-tmp/gcloud"]

        overview.on_selection_list_selection_toggled(event)

        event.selection_list.select.assert_any_call(
            "builtin:extension:gcloud:/test-tmp/gcloud"
        )
        event.selection_list.select.assert_any_call(
            "builtin:extension:gcloud:/test-tmp/boto"
        )

    def test_refresh_from_updates_overview_widgets(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        shell = mock.Mock()
        shell.styles = mock.Mock()
        base_button = mock.Mock()
        extensions_button = mock.Mock()
        extras_button = mock.Mock()
        shares_overview = mock.Mock()
        shares_title = mock.Mock()
        shares_list = mock.Mock()
        docker_title = mock.Mock()
        docker_list = mock.Mock()

        def query_one_side_effect(selector: str, _expected_type: object) -> mock.Mock:
            return {
                "#shell": shell,
                "#base": base_button,
                "#extensions": extensions_button,
                "#extras": extras_button,
                "#shares_overview": shares_overview,
                "#shares_overview_title": shares_title,
                "#shares_overview_list": shares_list,
                "#docker_overview_title": docker_title,
                "#docker_overview_list": docker_list,
            }[selector]

        overview.query_one = mock.Mock(side_effect=query_one_side_effect)
        draft = _build_draft(
            AgentConfig(base="ubuntu"),
            ParsedArgs(False, "", "codex", [], False, [], None),
        )

        with (
            mock.patch.object(
                type(overview),
                "size",
                new_callable=mock.PropertyMock,
                return_value=mock.Mock(width=120),
            ),
            mock.patch(
                "aicage.runtime.menu.textual.overview.view.shares_values"
            ) as shares_values,
        ):
            shares_values.return_value = mock.Mock(built_in_shares=[])
            overview.refresh_from(draft, _build_context())

        self.assertEqual("Base\nubuntu", base_button.label)
        self.assertEqual("Extensions\nnone", extensions_button.label)
        self.assertEqual("Docker Args\nnone", extras_button.label)

    def test_apply_shell_width_sets_fixed_width(self) -> None:
        overview = Overview(
            "codex",
            "/test-tmp/project",
            OverviewState(
                None,
                [
                    BuiltInShareValue(
                        "git_support", "ssh", "SSH", "/test-tmp/.ssh", None, True
                    )
                ],
                [CustomShareValue("/test-tmp/logs")],
                False,
            ),
        )
        shell = mock.Mock()
        shell.styles = mock.Mock()
        overview.query_one = mock.Mock(return_value=shell)

        overview.apply_shell_width(120)

        self.assertEqual(shell.styles.width, shell.styles.min_width)
        self.assertEqual(shell.styles.width, shell.styles.max_width)

    def test_focus_default_focuses_ok_button(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        button = mock.Mock(spec=Button)
        overview.query_one = mock.Mock(return_value=button)

        overview.focus_default()

        button.focus.assert_called_once_with()

    def test_focus_section_focuses_section_button(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        button = mock.Mock(spec=Button)
        overview.query_one = mock.Mock(return_value=button)

        overview.focus_section("base")

        button.focus.assert_called_once_with()

    def test_hide_shell_hides_shell(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        shell = mock.Mock()
        overview.query_one = mock.Mock(return_value=shell)

        overview.hide_shell()

        self.assertFalse(shell.display)

    def test_show_shell_shows_shell(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        shell = mock.Mock()
        overview.query_one = mock.Mock(return_value=shell)

        overview.show_shell()

        self.assertTrue(shell.display)

    def test_current_built_in_shares_returns_selected_state(self) -> None:
        overview = Overview(
            "codex",
            "/test-tmp/project",
            OverviewState(
                None,
                [
                    BuiltInShareValue(
                        "git_support", "ssh", "SSH", "/test-tmp/.ssh", None, False
                    )
                ],
                [],
                False,
            ),
        )
        selection_list = mock.Mock(spec=SelectionList)
        selection_list.selected = ["builtin:git_support:ssh"]
        overview.query_one = mock.Mock(return_value=selection_list)

        values = overview.current_built_in_shares()

        self.assertTrue(values[0].enabled)

    def test_current_custom_shares_returns_copy(self) -> None:
        state = OverviewState(None, [], [CustomShareValue("/test-tmp/logs")], False)
        overview = Overview("codex", "/test-tmp/project", state)

        values = overview.current_custom_shares()

        self.assertEqual(state.custom_shares, values)
        self.assertIsNot(state.custom_shares, values)

    def test_current_docker_socket_enabled_returns_selected_state(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        selection_list = mock.Mock(spec=SelectionList)
        selection_list.selected = ["docker:socket"]
        overview.query_one = mock.Mock(return_value=selection_list)

        value = overview.current_docker_socket_enabled(False)

        self.assertTrue(value.enabled)


class OverviewAsyncTests(IsolatedAsyncioTestCase):
    async def test_on_button_pressed_posts_section_message(self) -> None:
        overview = Overview(
            "codex", "/test-tmp/project", OverviewState(None, [], [], False)
        )
        overview.post_message = mock.Mock()
        event = mock.Mock()
        event.button.id = "base"

        overview.on_button_pressed(event)

        self.assertIsInstance(
            overview.post_message.call_args.args[0], Overview.EditSectionRequested
        )
