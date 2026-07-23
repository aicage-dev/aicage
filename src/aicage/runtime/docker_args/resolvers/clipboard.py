import os
from pathlib import Path

from aicage.cli_types import ParsedArgs
from aicage.config.context import ConfigContext
from aicage.config.project_config import AgentConfig
from aicage.runtime.docker_args.support.resolver_types import MountRequest, ResolvedArgs
from aicage.runtime.run_args import EnvVar

_DISPLAY = "DISPLAY"
_WAYLAND_DISPLAY = "WAYLAND_DISPLAY"
_XAUTHORITY = "XAUTHORITY"
_XDG_RUNTIME_DIR = "XDG_RUNTIME_DIR"
_X11_SOCKET_DIR = Path(
    "/tmp/.X11-unix"
)  # nosec B108 -- X11 sockets live at this fixed host path.


def describe_host_clipboard_access() -> str:
    if os.name == "nt":
        return "Not supported on Windows hosts."
    resolved = _resolve_host_clipboard_access()
    if resolved is None:
        return "No supported Linux host clipboard detected."
    _args, description = resolved
    return description


def resolve(
    context: ConfigContext,
    agent: str,
    parsed: ParsedArgs | None,
) -> ResolvedArgs:
    _ = parsed
    agent_cfg: AgentConfig = context.project_cfg.agents[agent]
    if agent_cfg.mounts.clipboard is not True or os.name == "nt":
        return ResolvedArgs()
    resolved = _resolve_host_clipboard_access()
    return ResolvedArgs() if resolved is None else resolved[0]


def _resolve_host_clipboard_access() -> tuple[ResolvedArgs, str] | None:
    wayland = _resolve_wayland()
    if wayland is not None:
        return wayland
    return _resolve_x11()


def _resolve_wayland() -> tuple[ResolvedArgs, str] | None:
    runtime_dir = os.environ.get(_XDG_RUNTIME_DIR)
    display = os.environ.get(_WAYLAND_DISPLAY)
    if not runtime_dir or not display:
        return None
    socket_path = Path(runtime_dir) / display
    if not socket_path.exists():
        return None
    return (
        ResolvedArgs(
            mounts=[MountRequest(host_path=socket_path)],
            env=[
                EnvVar(name=_XDG_RUNTIME_DIR, value=runtime_dir),
                EnvVar(name=_WAYLAND_DISPLAY, value=display),
            ],
        ),
        f"Wayland socket {socket_path}; env {_XDG_RUNTIME_DIR}, {_WAYLAND_DISPLAY}",
    )


def _resolve_x11() -> tuple[ResolvedArgs, str] | None:
    display = os.environ.get(_DISPLAY)
    if not display or not _X11_SOCKET_DIR.exists():
        return None
    mounts = [MountRequest(host_path=_X11_SOCKET_DIR)]
    env = [EnvVar(name=_DISPLAY, value=display)]
    details = [f"X11 socket {_X11_SOCKET_DIR}", f"env {_DISPLAY}"]
    xauthority = os.environ.get(_XAUTHORITY)
    if xauthority:
        xauthority_path = Path(xauthority)
        if xauthority_path.is_file():
            mounts.append(MountRequest(host_path=xauthority_path, read_only=True))
            env.append(EnvVar(name=_XAUTHORITY, value=xauthority))
            details.append(f"read-only {_XAUTHORITY} {xauthority_path}")
    return ResolvedArgs(mounts=mounts, env=env), "; ".join(details)
