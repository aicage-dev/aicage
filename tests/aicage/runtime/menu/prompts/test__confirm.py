from unittest import TestCase, mock

from aicage.config.project_config import (
    MOUNT_GITCONFIG_KEY,
    MOUNT_GITROOT_KEY,
    MOUNT_GNUPG_KEY,
    MOUNT_SSH_KEY,
)
from aicage.runtime._errors import RuntimeExecutionError
from aicage.runtime.menu.prompts import _confirm as confirm


class PromptConfirmTests(TestCase):
    def test__prompt_yes_no_accepts_default(self) -> None:
        with (
            mock.patch("aicage.runtime.menu.prompts._confirm.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value=""),
        ):
            self.assertTrue(confirm._prompt_yes_no("Continue?", default=True))
            self.assertFalse(confirm._prompt_yes_no("Continue?", default=False))

    def test__prompt_yes_no_parses_response(self) -> None:
        with (
            mock.patch("aicage.runtime.menu.prompts._confirm.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="y"),
        ):
            self.assertTrue(confirm._prompt_yes_no("Continue?", default=False))

    def test_prompt_persist_docker_socket_delegates(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.prompts._confirm._prompt_yes_no", return_value=True
        ) as prompt_mock:
            self.assertTrue(confirm.prompt_persist_docker_socket())
        prompt_mock.assert_called_once_with(
            "Persist mounting the Docker socket for this project?",
            default=True,
        )

    def test_prompt_mount_git_support_defaults_to_all(self) -> None:
        git_items = [
            (MOUNT_GITCONFIG_KEY, "Git config (name/email): /test-tmp/gitconfig"),
            (MOUNT_GITROOT_KEY, "Git root (repository access): /test-tmp/root"),
        ]
        with (
            mock.patch("aicage.runtime.menu.prompts._confirm.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value=""),
        ):
            selected = confirm.prompt_mount_git_support(git_items, [])
        self.assertEqual([MOUNT_GITCONFIG_KEY, MOUNT_GITROOT_KEY], selected)

    def test_prompt_mount_git_support_accepts_selection(self) -> None:
        git_items = [
            (MOUNT_GITCONFIG_KEY, "Git config (name/email): /test-tmp/gitconfig"),
            (MOUNT_GNUPG_KEY, "GnuPG keys (for Git signing): /test-tmp/gnupg"),
            (MOUNT_SSH_KEY, "SSH keys (for Git SSH/signing): /test-tmp/ssh"),
        ]
        with (
            mock.patch("aicage.runtime.menu.prompts._confirm.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value="1,3"),
        ):
            selected = confirm.prompt_mount_git_support(git_items, [])
        self.assertEqual([MOUNT_GITCONFIG_KEY, MOUNT_SSH_KEY], selected)

    def test_prompt_mount_git_support_renders_extension_section(self) -> None:
        git_items = [
            (MOUNT_GITCONFIG_KEY, "Git config (name/email): /test-tmp/gitconfig")
        ]
        extension_items = [("gh", "Extension gh shares: /test-tmp/gh")]
        with (
            mock.patch("aicage.runtime.menu.prompts._confirm.ensure_tty_for_prompt"),
            mock.patch("builtins.input", return_value=""),
            mock.patch("builtins.print") as print_mock,
        ):
            selected = confirm.prompt_mount_git_support(git_items, extension_items)

        self.assertEqual([MOUNT_GITCONFIG_KEY, "gh"], selected)
        printed_lines = [
            args[0] if args else "" for args, _ in print_mock.call_args_list
        ]
        self.assertIn("Enable Git support in the container by mounting:", printed_lines)
        self.assertIn("Mounts from extensions:", printed_lines)

    def test_parse_number_selection_rejects_invalid_value(self) -> None:
        with self.assertRaises(RuntimeExecutionError) as context:
            confirm._parse_number_selection("0", 3)
        self.assertIn("Pick a number between 1 and 3.", str(context.exception))

    def test_parse_number_selection_rejects_duplicates(self) -> None:
        with self.assertRaises(RuntimeExecutionError) as context:
            confirm._parse_number_selection("2,2", 3)
        self.assertIn("Duplicate selection '2' is not allowed.", str(context.exception))

    def test_prompt_persist_docker_args_replaces_existing(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.prompts._confirm._prompt_yes_no", return_value=True
        ) as prompt_mock:
            self.assertTrue(confirm.prompt_persist_docker_args("-it", "--rm"))
        prompt_mock.assert_called_once_with(
            "Persist docker run args '-it' for this project (replacing '--rm')?",
            default=True,
        )

    def test_prompt_persist_shares_adds_shares(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.prompts._confirm._prompt_yes_no", return_value=True
        ) as prompt_mock:
            self.assertTrue(
                confirm.prompt_persist_shares(
                    ["/test-tmp/share"], ["/test-tmp/one", "/test-tmp/two:ro"]
                )
            )
        prompt_mock.assert_called_once_with(
            "Persist share mounts '/test-tmp/share' for this project (adding to 2 existing share(s))?",
            default=True,
        )

    def test_prompt_update_aicage_delegates(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.prompts._confirm._prompt_yes_no", return_value=True
        ) as prompt_mock:
            self.assertTrue(confirm.prompt_update_aicage("0.9.4", "0.9.5"))
        prompt_mock.assert_called_once_with(
            "A newer version of aicage is available (installed: 0.9.4, latest: 0.9.5). Update now?",
            default=True,
        )

    def test_prompt_update_image_delegates(self) -> None:
        with mock.patch(
            "aicage.runtime.menu.prompts._confirm._prompt_yes_no", return_value=True
        ) as prompt_mock:
            self.assertTrue(
                confirm.prompt_update_image("ghcr.io/aicage/aicage:codex-fedora")
            )
        prompt_mock.assert_called_once_with(
            "A newer version of Docker image 'ghcr.io/aicage/aicage:codex-fedora' is available. Pull now?",
            default=True,
        )
