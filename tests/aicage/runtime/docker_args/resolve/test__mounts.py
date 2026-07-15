import tempfile
from pathlib import Path
from unittest import TestCase

from aicage.paths import container_project_path
from aicage.runtime.docker_args.resolve._mounts import map_mount_requests
from aicage.runtime.docker_args.support.resolver_types import MountRequest
from aicage.runtime.run_args import MountSpec


class MountsTests(TestCase):
    def test_map_mount_requests_deduplicates_nested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir).resolve()
            parent_path = root_path / "parent"
            child_path = parent_path / "child"
            parent_path.mkdir()
            child_path.mkdir()

            mounts = map_mount_requests(
                [
                    MountRequest(host_path=child_path, read_only=False),
                    MountRequest(host_path=parent_path, read_only=False),
                ]
            )

        self.assertEqual(
            [
                MountSpec(
                    host_path=parent_path,
                    container_path=container_project_path(parent_path),
                    read_only=False,
                )
            ],
            mounts,
        )

    def test_map_mount_requests_deduplicates_exact_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir).resolve()
            project_path = root_path / "project"
            project_path.mkdir()

            mounts = map_mount_requests(
                [
                    MountRequest(host_path=project_path, read_only=False),
                    MountRequest(host_path=project_path, read_only=False),
                ]
            )

        self.assertEqual(
            [
                MountSpec(
                    host_path=project_path,
                    container_path=container_project_path(project_path),
                    read_only=False,
                )
            ],
            mounts,
        )

    def test_map_mount_requests_skips_nested_child_when_parent_selected_first(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir).resolve()
            parent_path = root_path / "parent"
            child_path = parent_path / "child"
            parent_path.mkdir()
            child_path.mkdir()

            mounts = map_mount_requests(
                [
                    MountRequest(host_path=parent_path, read_only=False),
                    MountRequest(host_path=child_path, read_only=False),
                ]
            )

        self.assertEqual(
            [
                MountSpec(
                    host_path=parent_path,
                    container_path=container_project_path(parent_path),
                    read_only=False,
                )
            ],
            mounts,
        )

    def test_map_mount_requests_keeps_nested_child_when_read_only_differs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir).resolve()
            parent_path = root_path / "parent"
            child_path = parent_path / "child"
            parent_path.mkdir()
            child_path.mkdir()

            mounts = map_mount_requests(
                [
                    MountRequest(host_path=parent_path, read_only=False),
                    MountRequest(host_path=child_path, read_only=True),
                ]
            )

        self.assertEqual(
            [
                MountSpec(
                    host_path=parent_path,
                    container_path=container_project_path(parent_path),
                    read_only=False,
                ),
                MountSpec(
                    host_path=child_path,
                    container_path=container_project_path(child_path),
                    read_only=True,
                ),
            ],
            mounts,
        )

    def test_map_mount_requests_keeps_nested_parent_when_read_only_differs(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir).resolve()
            parent_path = root_path / "parent"
            child_path = parent_path / "child"
            parent_path.mkdir()
            child_path.mkdir()

            mounts = map_mount_requests(
                [
                    MountRequest(host_path=child_path, read_only=False),
                    MountRequest(host_path=parent_path, read_only=True),
                ]
            )

        self.assertEqual(
            [
                MountSpec(
                    host_path=parent_path,
                    container_path=container_project_path(parent_path),
                    read_only=True,
                ),
                MountSpec(
                    host_path=child_path,
                    container_path=container_project_path(child_path),
                    read_only=False,
                ),
            ],
            mounts,
        )
