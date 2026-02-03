import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import ProjectConfig
from aicage.runtime.docker_args import _shares
from aicage.runtime.docker_args._resolver_types import MountRequest, ResolvedArgs


class ShareResolverTests(TestCase):
    def test_resolve_returns_share_mounts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            cwd = Path(tmp_dir)
            parsed = ParsedArgs(False, "", "codex", [], False, ["data:ro"], None)
            context = ConfigContext(
                store=mock.Mock(),
                project_cfg=ProjectConfig(path=str(cwd / "project"), agents={}),
                agents={},
                bases={},
                extensions={},
            )

            with mock.patch("aicage.runtime.docker_args._shares.Path.cwd", return_value=cwd):
                resolved = _shares.resolve(context, "codex", parsed)

        expected_path = (cwd / "data").resolve()
        self.assertEqual(
            ResolvedArgs(mounts=[MountRequest(host_path=expected_path, read_only=True)]),
            resolved,
        )
