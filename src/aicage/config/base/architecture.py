import platform


def _host_architecture() -> str | None:
    machine = platform.machine().strip().lower()
    if machine in {"x86_64", "amd64"}:
        return "amd64"
    if machine in {"aarch64", "arm64"}:
        return "arm64"
    return None


def base_supports_host_architecture(architectures: list[str]) -> bool:
    host = _host_architecture()
    if host is None:
        return True
    return host in architectures
