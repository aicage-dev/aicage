from pathlib import Path

import pytest

from aicage.config.config_store import SettingsStore
from aicage.config.project_config import AgentConfig, _ProjectConfig
from aicage.constants import DEFAULT_EXTENDED_IMAGE_NAME

from ._helpers import (
    assert_marker_extension_ready,
    copy_marker_extension_sample,
    custom_extensions_dir,
    marker_shared_extension_dir,
    require_integration,
    run_cli_pty,
    setup_workspace,
)

pytestmark = pytest.mark.integration


def test_inherited_docker_args_apply_with_local_docker_args(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "copilot")
    store = SettingsStore()
    store.save_tree(
        workspace.parent,
        _ProjectConfig(
            path=str(workspace.parent),
            agents={
                "copilot": AgentConfig(
                    docker_args=(
                        "--env AICAGE_ENTRYPOINT_CMD=bash "
                        "--env INHERITED_CONFIG_VALUE=inherited"
                    )
                )
            },
        ),
    )
    project_cfg = store.load_project(workspace)
    project_cfg.agents["copilot"].docker_args = "--env LOCAL_CONFIG_VALUE=local"
    store.save_project(workspace, project_cfg)

    exit_code, output = run_cli_pty(
        [
            "--menu",
            "none",
            "copilot",
            "-lc",
            'test "$INHERITED_CONFIG_VALUE" = inherited '
            '&& test "$LOCAL_CONFIG_VALUE" = local',
        ],
        env=env,
        cwd=workspace,
    )

    assert exit_code == 0, output


def test_inherited_extension_runs_from_child_workspace(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    require_integration()
    workspace, env = setup_workspace(monkeypatch, tmp_path, "codex")
    marker_shared_extension_dir(Path(env["HOME"])).mkdir(parents=True, exist_ok=True)
    copy_marker_extension_sample(custom_extensions_dir() / "marker")
    store = SettingsStore()
    store.save_tree(
        workspace.parent,
        _ProjectConfig(
            path=str(workspace.parent),
            agents={
                "codex": AgentConfig(
                    image_ref=f"{DEFAULT_EXTENDED_IMAGE_NAME}:codex-ubuntu-marker",
                    extensions=["marker"],
                    extension_mounts={"marker": True},
                )
            },
        ),
    )

    assert_marker_extension_ready(env, workspace, "codex")
