from pathlib import Path

from aicage._logging import get_logger
from aicage.config.base.models import BaseMetadata
from aicage.constants import LOCAL_IMAGE_BASE_REPOSITORY
from aicage.docker.build import run_custom_base_build
from aicage.docker.query import (
    cleanup_old_digest,
    get_local_repo_digest_for_repo,
    local_image_exists,
)
from aicage.registry._build_flow import maybe_build
from aicage.registry._layers import base_layer_missing
from aicage.registry._time import now_iso
from aicage.registry.digest.remote_digest import get_remote_digest

from ._logs import build_log_path
from ._store import BuildRecord, BuildStore


def image_ref(base: str) -> str:
    return f"{LOCAL_IMAGE_BASE_REPOSITORY}:{base}"


def ensure(base: str, base_metadata: BaseMetadata, base_dir: Path) -> None:
    target_image_ref = image_ref(base)
    local_exists = local_image_exists(target_image_ref)
    store = BuildStore()
    source_digest = get_remote_digest(base_metadata.from_image)

    maybe_build(
        load_record=lambda: store.load(base),
        should_rebuild=lambda record: _should_rebuild(
            local_exists=local_exists,
            record=record,
            base_metadata=base_metadata,
            source_digest=source_digest,
            target_image_ref=target_image_ref,
        ),
        run_build=lambda: _run_build(
            base=base,
            base_metadata=base_metadata,
            base_dir=base_dir,
            target_image_ref=target_image_ref,
        ),
        save_record=lambda: store.save(
            BuildRecord(
                base=base,
                from_image=base_metadata.from_image,
                from_image_digest=source_digest or "",
                image_ref=target_image_ref,
                built_at=now_iso(),
            )
        ),
    )


def _should_rebuild(
    local_exists: bool,
    record: BuildRecord | None,
    base_metadata: BaseMetadata,
    source_digest: str | None,
    target_image_ref: str,
) -> bool:
    if not local_exists or record is None:
        return True
    if record.from_image != base_metadata.from_image:
        return True
    if source_digest and record.from_image_digest != source_digest:
        return True
    is_missing = base_layer_missing(base_metadata.from_image, target_image_ref)
    if is_missing is None:
        logger = get_logger()
        logger.warning(
            "Skipping base image layer validation for %s; missing local layer data.",
            target_image_ref,
        )
        return False
    return is_missing


def _run_build(
    base: str,
    base_metadata: BaseMetadata,
    base_dir: Path,
    target_image_ref: str,
) -> None:
    old_digest = get_local_repo_digest_for_repo(target_image_ref, LOCAL_IMAGE_BASE_REPOSITORY)
    log_path = build_log_path(base)
    run_custom_base_build(
        dockerfile_path=base_dir / "Dockerfile",
        build_root=base_dir,
        from_image=base_metadata.from_image,
        image_ref=target_image_ref,
        log_path=log_path,
    )
    cleanup_old_digest(LOCAL_IMAGE_BASE_REPOSITORY, old_digest, target_image_ref)
