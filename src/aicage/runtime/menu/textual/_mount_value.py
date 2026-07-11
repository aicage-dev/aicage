def split_mount_value(value: str) -> tuple[str, bool]:
    stripped = value.strip()
    if stripped.endswith(":ro"):
        return stripped[:-3], True
    return stripped, False


def compose_mount_value(path: str, read_only: bool) -> str:
    normalized_path, _ = split_mount_value(path)
    return f"{normalized_path}:ro" if read_only else normalized_path


def display_mount_value(value: str) -> str:
    parts = [part.strip() for part in value.split(",")]
    formatted_parts: list[str] = []
    for part in parts:
        path, read_only = split_mount_value(part)
        formatted_parts.append(f"Read-only: {path}" if read_only else path)
    return ", ".join(formatted_parts)
