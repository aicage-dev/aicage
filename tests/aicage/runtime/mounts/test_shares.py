import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.errors import AicageError
from aicage.paths import container_project_path
from aicage.runtime.mounts.shares import merge_share_values, resolve_share_mounts
from aicage.runtime.run_args import MountSpec


class ShareMountsTests(TestCase):
    def test_merge_share_values_merges_cli_over_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            existing = [f"{cwd / 'shared'}:ro", str(cwd / 'existing')]
            cli = ["shared", "new"]

            merged, new_shares = merge_share_values(cli, existing, cwd)

        self.assertEqual(
            [str(cwd / "shared"), str(cwd / "new"), str(cwd / "existing")],
            merged,
        )
        self.assertEqual([str(cwd / "new")], new_shares)

    def test_merge_share_values_deduplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            cli = ["data", "data:ro"]

            merged, new_shares = merge_share_values(cli, [], cwd)

        self.assertEqual([str(cwd / "data")], merged)
        self.assertEqual([str(cwd / "data")], new_shares)
    def test_resolve_share_mounts_resolves_relative_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            share_dir = cwd / "data"
            share_dir.mkdir()
            parsed = ParsedArgs(False, "", "codex", [], False, ["data"], None)

            with mock.patch("aicage.runtime.mounts.shares.Path.cwd", return_value=cwd):
                mounts = resolve_share_mounts(parsed, cwd, [], [])

        self.assertEqual(1, len(mounts))
        self.assertEqual(share_dir.resolve(), mounts[0].host_path)
        self.assertEqual(container_project_path(share_dir.resolve()), mounts[0].container_path)
        self.assertFalse(mounts[0].read_only)

    def test_resolve_share_mounts_sets_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            share_dir = cwd / "data"
            share_dir.mkdir()
            parsed = ParsedArgs(False, "", "codex", [], False, ["data:ro"], None)

            with mock.patch("aicage.runtime.mounts.shares.Path.cwd", return_value=cwd):
                mounts = resolve_share_mounts(parsed, cwd, [], [])

        self.assertEqual(1, len(mounts))
        self.assertTrue(mounts[0].read_only)

    def test_resolve_share_mounts_skips_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            project_path = cwd / "project"
            project_path.mkdir()
            shared_dir = cwd / "shared"
            shared_dir.mkdir()
            existing_dir = cwd / "existing"
            existing_dir.mkdir()
            agent_dir = cwd / "agent"
            agent_dir.mkdir()
            parsed = ParsedArgs(
                False,
                "",
                "codex",
                [],
                False,
                ["project", "existing", "agent", "shared"],
                None,
            )
            existing_mounts = [
                MountSpec(host_path=existing_dir, container_path=container_project_path(existing_dir)),
            ]
            agent_mounts = [
                MountSpec(host_path=agent_dir, container_path=container_project_path(agent_dir)),
            ]

            with mock.patch("aicage.runtime.mounts.shares.Path.cwd", return_value=cwd):
                mounts = resolve_share_mounts(parsed, project_path, existing_mounts, agent_mounts)

        self.assertEqual(1, len(mounts))
        self.assertEqual(shared_dir.resolve(), mounts[0].host_path)

    def test_resolve_share_mounts_creates_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            parsed = ParsedArgs(False, "", "codex", [], False, ["missing"], None)

            with mock.patch("aicage.runtime.mounts.shares.Path.cwd", return_value=cwd):
                mounts = resolve_share_mounts(parsed, cwd, [], [])

            self.assertEqual(1, len(mounts))
            self.assertTrue((cwd / "missing").is_dir())

    def test_resolve_share_mounts_creates_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            parsed = ParsedArgs(False, "", "codex", [], False, ["missing.txt"], None)

            with mock.patch("aicage.runtime.mounts.shares.Path.cwd", return_value=cwd):
                mounts = resolve_share_mounts(parsed, cwd, [], [])

            self.assertEqual(1, len(mounts))
            self.assertTrue((cwd / "missing.txt").is_file())

    def test_resolve_share_mounts_rejects_destination(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            parsed = ParsedArgs(False, "", "codex", [], False, ["data:/dst"], None)

            with (
                mock.patch("aicage.runtime.mounts.shares.Path.cwd", return_value=cwd),
                self.assertRaises(AicageError) as ctx,
            ):
                resolve_share_mounts(parsed, cwd, [], [])

        self.assertIn("Share destinations are not supported", str(ctx.exception))
