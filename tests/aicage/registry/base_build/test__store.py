import tempfile
from pathlib import Path
from unittest import TestCase, mock

from aicage.registry.base_build._store import (
    BuildRecord,
    BuildStore,
)


class BuildStoreTests(TestCase):
    def test_load_returns_none_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            with mock.patch(
                "aicage.registry.base_build._store.paths_module.BASE_IMAGE_BUILD_STATE_DIR",
                base_dir,
            ):
                store = BuildStore()
                self.assertIsNone(store.load("missing"))

    def test_save_persists_record(self) -> None:
        record = BuildRecord(
            base="custom",
            from_image="ubuntu:latest",
            from_image_digest="sha256:deadbeef",
            image_ref="aicage-image-base:custom",
            built_at="2024-01-01T00:00:00+00:00",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            with mock.patch(
                "aicage.registry.base_build._store.paths_module.BASE_IMAGE_BUILD_STATE_DIR",
                base_dir,
            ):
                store = BuildStore()

                path = store.save(record)
                loaded = store.load("custom")

                self.assertTrue(path.is_file())
                self.assertEqual(record, loaded)
