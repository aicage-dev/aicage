from pathlib import Path


def looks_like_file(path_value: str) -> bool:
    return bool(Path(path_value).suffix)


def ensure_path_exists(path: Path, looks_like_file_path: bool) -> Path:
    if path.exists():
        if not path.is_file() and not path.is_dir():
            raise ValueError(f"Path exists but is not a file or directory: {path}")
        return path
    if looks_like_file_path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    else:
        path.mkdir(parents=True, exist_ok=True)
    return path
