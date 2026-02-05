from pathlib import Path


def ensure_path_exists(path: Path, is_file: bool) -> Path:
    if path.exists():
        if not path.is_file() and not path.is_dir():
            raise ValueError(f"Path exists but is not a file or directory: {path}")
        return path
    if is_file:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    else:
        path.mkdir(parents=True, exist_ok=True)
    return path
