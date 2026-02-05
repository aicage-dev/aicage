import tempfile
from pathlib import Path
from unittest import TestCase

from aicage.runtime._path_utils import ensure_path_exists


class PathUtilsTests(TestCase):
    def test_ensure_path_exists_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "config.yml"

            ensure_path_exists(file_path, True)

            self.assertTrue(file_path.is_file())

    def test_ensure_path_exists_creates_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            dir_path = Path(tmp_dir) / "config"

            ensure_path_exists(dir_path, False)

            self.assertTrue(dir_path.is_dir())
