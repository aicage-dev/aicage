import tempfile
from pathlib import Path
from unittest import TestCase, mock

import yaml

from aicage.config.base.models import BaseMetadata
from aicage.constants import LOCAL_IMAGE_BASE_REPOSITORY
from aicage.docker.errors import DockerError
from aicage.registry.local_build import _custom_base
from aicage.registry.local_build._custom_base_store import (
    CustomBaseBuildRecord,
    CustomBaseBuildStore,
)


class EnsureCustomBaseImageTests(TestCase):
    def test_custom_base_image_ref_uses_base_repository(self) -> None:
        self.assertEqual(
            f"{LOCAL_IMAGE_BASE_REPOSITORY}:custom",
            _custom_base.custom_base_image_ref("custom"),
        )

    def test_ensure_custom_base_image_builds_when_missing(self) -> None:
        base_metadata = self._base_metadata()
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir) / "custom"
            base_dir.mkdir()
            (base_dir / "Dockerfile").write_text("FROM ${FROM_IMAGE}\n", encoding="utf-8")
            state_dir = Path(tmp_dir) / "state"
            with (
                mock.patch(
                    "aicage.registry.local_build._custom_base_store.paths_module.BASE_IMAGE_BUILD_STATE_DIR",
                    state_dir,
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.local_image_exists",
                    return_value=False,
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.get_remote_digest",
                    return_value="sha256:remote",
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.run_custom_base_build"
                ) as build_mock,
            ):
                _custom_base.ensure_custom_base_image("custom", base_metadata, base_dir)

            build_mock.assert_called_once()
            record_path = state_dir / "base-custom.yml"
            payload = yaml.safe_load(record_path.read_text(encoding="utf-8"))
            self.assertEqual("custom", payload["base"])
            self.assertEqual("sha256:remote", payload["from_image_digest"])

    def test_ensure_custom_base_image_skips_when_digest_matches(self) -> None:
        base_metadata = self._base_metadata()
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir) / "custom"
            base_dir.mkdir()
            (base_dir / "Dockerfile").write_text("FROM ${FROM_IMAGE}\n", encoding="utf-8")
            state_dir = Path(tmp_dir) / "state"
            with (
                mock.patch(
                    "aicage.registry.local_build._custom_base_store.paths_module.BASE_IMAGE_BUILD_STATE_DIR",
                    state_dir,
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.local_image_exists",
                    return_value=True,
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.get_remote_digest",
                    return_value="sha256:remote",
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.run_custom_base_build"
                ) as build_mock,
            ):
                store = CustomBaseBuildStore()
                store.save(
                    CustomBaseBuildRecord(
                        base="custom",
                        from_image=base_metadata.from_image,
                        from_image_digest="sha256:remote",
                        image_ref=_custom_base.custom_base_image_ref("custom"),
                        built_at="2024-01-01T00:00:00+00:00",
                    )
                )
                _custom_base.ensure_custom_base_image("custom", base_metadata, base_dir)

            build_mock.assert_not_called()

    def test_ensure_custom_base_image_warns_on_build_failure(self) -> None:
        base_metadata = self._base_metadata()
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir) / "custom"
            base_dir.mkdir()
            (base_dir / "Dockerfile").write_text("FROM ${FROM_IMAGE}\n", encoding="utf-8")
            state_dir = Path(tmp_dir) / "state"
            with (
                mock.patch(
                    "aicage.registry.local_build._custom_base_store.paths_module.BASE_IMAGE_BUILD_STATE_DIR",
                    state_dir,
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.local_image_exists",
                    return_value=True,
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.get_remote_digest",
                    return_value="sha256:remote",
                ),
                mock.patch(
                    "aicage.registry.local_build._custom_base.run_custom_base_build",
                    side_effect=DockerError("build failed"),
                ),
            ):
                _custom_base.ensure_custom_base_image("custom", base_metadata, base_dir)

    def test_ensure_custom_base_image_cleans_up_old_digest(self) -> None:
        base_metadata = BaseMetadata(
            from_image="ubuntu:latest",
            base_image_distro="Ubuntu",
            base_image_description="Custom",
            build_local=True,
            local_definition_dir=Path("/tmp/custom-base"),
        )
        with (
            mock.patch(
                "aicage.registry.local_build._custom_base.local_image_exists",
                return_value=True,
            ),
            mock.patch(
                "aicage.registry.local_build._custom_base.CustomBaseBuildStore"
            ) as store_cls,
            mock.patch(
                "aicage.registry.local_build._custom_base._should_build",
                return_value=True,
            ),
            mock.patch(
                "aicage.registry.local_build._custom_base.run_custom_base_build"
            ) as build_mock,
            mock.patch(
                "aicage.registry.local_build._custom_base.get_remote_digest",
                return_value="sha256:remote",
            ),
            mock.patch(
                "aicage.registry.local_build._custom_base.get_local_repo_digest_for_repo",
                return_value="sha256:old",
            ),
            mock.patch(
                "aicage.registry.local_build._custom_base.cleanup_old_digest"
            ) as cleanup_mock,
            mock.patch(
                "aicage.registry.local_build._custom_base.custom_base_log_path",
                return_value=Path("/tmp/logs/custom-base.log"),
            ),
            mock.patch(
                "aicage.registry.local_build._custom_base.now_iso",
                return_value="2024-01-01T00:00:00+00:00",
            ),
        ):
            store_cls.return_value.load.return_value = None
            _custom_base.ensure_custom_base_image("custom", base_metadata, Path("/tmp/custom-base"))

        build_mock.assert_called_once()
        cleanup_mock.assert_called_once_with(
            LOCAL_IMAGE_BASE_REPOSITORY,
            "sha256:old",
            f"{LOCAL_IMAGE_BASE_REPOSITORY}:custom",
        )

    @staticmethod
    def _base_metadata() -> BaseMetadata:
        return BaseMetadata(
            from_image="ubuntu:latest",
            base_image_distro="Ubuntu",
            base_image_description="Custom",
            build_local=True,
            local_definition_dir=Path("/tmp/base"),
        )
