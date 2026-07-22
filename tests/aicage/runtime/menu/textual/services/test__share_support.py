from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.project_config import AgentConfig
from aicage.runtime.menu.textual._models import BuiltInShareValue
from aicage.runtime.menu.textual.services import _share_support

from ..._test_support import _build_context, _build_draft


class ShareSupportTests(TestCase):
    def test_normalize_shares_from_editor_returns_normalized_values(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
            project_path=Path("/repo"),
        )

        values = _share_support.normalize_shares_from_editor(draft, ["logs:ro"])

        self.assertEqual(["/repo/logs:ro"], values)

    def test_built_in_share_values_returns_only_relevant_items(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
            project_path=Path("/project"),
        )
        with (
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_git_config_path",
                return_value=Path("/test-tmp/gitconfig"),
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_git_root",
                return_value=Path("/repo"),
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.is_commit_signing_enabled",
                return_value=False,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_signing_format",
                return_value=None,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.uses_ssh_remotes",
                return_value=False,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_ssh_dir",
                return_value=Path("/test-tmp/ssh"),
            ),
            mock.patch("pathlib.Path.exists", return_value=True),
        ):
            values = _share_support.built_in_share_values(
                draft, _build_context().extensions
            )

        self.assertEqual(
            [
                BuiltInShareValue(
                    "git_support",
                    "gitconfig",
                    "Git config",
                    "/test-tmp/gitconfig",
                    None,
                    True,
                ),
                BuiltInShareValue(
                    "git_support", "gitroot", "Git root", "/repo", None, True
                ),
            ],
            values,
        )

    def test_built_in_share_values_include_selected_extension_shares(self) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu", extensions=["gh"]),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
            project_path=Path("/project"),
        )

        values = _share_support.built_in_share_values(
            draft, _build_context().extensions
        )

        self.assertEqual(
            [
                BuiltInShareValue(
                    "extension",
                    "gh",
                    "Extension gh",
                    str(Path.home().resolve() / ".config/gh"),
                    None,
                    True,
                )
            ],
            [item for item in values if item.source == "extension"],
        )

    def test_built_in_share_values_split_multiple_extension_shares_into_rows(
        self,
    ) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu", extensions=["gcloud"]),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
            project_path=Path("/project"),
        )

        values = _share_support.built_in_share_values(
            draft, _build_context().extensions
        )

        self.assertEqual(
            [
                BuiltInShareValue(
                    "extension",
                    "gcloud",
                    "Extension gcloud",
                    str(Path.home().resolve() / ".config/gcloud"),
                    None,
                    True,
                    f"gcloud:{Path.home().resolve() / '.config/gcloud'}",
                ),
                BuiltInShareValue(
                    "extension",
                    "gcloud",
                    "Extension gcloud",
                    str(Path.home().resolve() / ".boto"),
                    None,
                    True,
                    f"gcloud:{Path.home().resolve() / '.boto'}",
                ),
            ],
            [item for item in values if item.source == "extension"],
        )

    def test_built_in_share_values_includes_ssh_mount_when_ssh_signing_enabled(
        self,
    ) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
            project_path=Path("/project"),
        )
        with (
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_git_config_path",
                return_value=None,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_git_root",
                return_value=None,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.is_commit_signing_enabled",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_signing_format",
                return_value="ssh",
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.uses_ssh_remotes",
                return_value=False,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_ssh_dir",
                return_value=Path("/test-tmp/ssh"),
            ),
            mock.patch("pathlib.Path.exists", return_value=True),
        ):
            values = _share_support.built_in_share_values(
                draft, _build_context().extensions
            )

        self.assertIn(
            BuiltInShareValue("git_support", "ssh", "SSH", "/test-tmp/ssh", None, True),
            values,
        )

    def test_built_in_share_values_includes_gnupg_mount_when_non_ssh_signing_enabled(
        self,
    ) -> None:
        draft = _build_draft(
            agent_cfg=AgentConfig(base="ubuntu"),
            parsed=ParsedArgs(False, "", "codex", [], False, [], None),
            project_path=Path("/project"),
        )
        with (
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_git_config_path",
                return_value=None,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_git_root",
                return_value=None,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.is_commit_signing_enabled",
                return_value=True,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_signing_format",
                return_value="openpgp",
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.uses_ssh_remotes",
                return_value=False,
            ),
            mock.patch(
                "aicage.runtime.menu.textual.services._share_support.resolve_gpg_home",
                return_value=Path("/test-tmp/gnupg"),
            ),
            mock.patch("pathlib.Path.exists", return_value=True),
        ):
            values = _share_support.built_in_share_values(
                draft, _build_context().extensions
            )

        self.assertIn(
            BuiltInShareValue(
                "git_support", "gnupg", "GnuPG", "/test-tmp/gnupg", None, True
            ),
            values,
        )
