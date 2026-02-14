import hashlib

from aicage.config.extensions.loader import ExtensionMetadata, extension_hash
from aicage.config.runtime_config import RunConfig
from aicage.constants import (
    DEFAULT_EXTENDED_IMAGE_NAME,
    LOCAL_IMAGE_BASE_REPOSITORY,
    LOCAL_IMAGE_REPOSITORY,
)
from aicage.docker.build import run_extended_build
from aicage.docker.query import (
    cleanup_old_digest,
    cleanup_source_image_tag,
    get_local_repo_digest_for_repo,
)
from aicage.docker.refs import repository_from_image_ref
from aicage.registry._errors import RegistryError
from aicage.registry._time import now_iso

from ._extended_plan import should_build_extended
from ._extended_store import ExtendedBuildRecord, ExtendedBuildStore
from ._logs import build_log_path_for_image


def ensure_extended_image(run_config: RunConfig) -> None:
    if not run_config.selection.extensions:
        raise RegistryError("No extensions selected for extended image build.")

    resolved = _resolve_extensions(run_config.selection.extensions, run_config.context.extensions)
    combined_hash = _combined_extension_hash(resolved)
    store = ExtendedBuildStore()
    record = store.load(run_config.selection.image_ref)
    needs_build = should_build_extended(
        run_config=run_config,
        record=record,
        base_image_ref=run_config.selection.base_image_ref,
        extension_hash=combined_hash,
    )
    if not needs_build:
        return

    image_ref = run_config.selection.image_ref
    image_repository = repository_from_image_ref(image_ref)
    old_digest = get_local_repo_digest_for_repo(image_ref, image_repository)
    log_path = build_log_path_for_image(image_ref)
    run_extended_build(
        run_config=run_config,
        base_image_ref=run_config.selection.base_image_ref,
        extensions=resolved,
        log_path=log_path,
    )
    cleanup_old_digest(image_repository, old_digest, image_ref)
    base_repository = repository_from_image_ref(run_config.selection.base_image_ref)
    if not _is_local_managed_repository(base_repository):
        cleanup_source_image_tag(run_config.selection.base_image_ref)
    store.save(
        ExtendedBuildRecord(
            agent=run_config.agent,
            base=run_config.selection.base,
            image_ref=image_ref,
            extensions=list(run_config.selection.extensions),
            extension_hash=combined_hash,
            base_image=run_config.selection.base_image_ref,
            built_at=now_iso(),
        )
    )


def _resolve_extensions(
    extension_ids: list[str],
    extensions: dict[str, ExtensionMetadata],
) -> list[ExtensionMetadata]:
    missing = [ext for ext in extension_ids if ext not in extensions]
    if missing:
        raise RegistryError(f"Missing extensions: {', '.join(sorted(missing))}.")
    return [extensions[ext] for ext in extension_ids]


def _combined_extension_hash(extensions: list[ExtensionMetadata]) -> str:
    digest = hashlib.sha256()
    for extension in extensions:
        digest.update(extension.extension_id.encode("utf-8"))
        digest.update(extension_hash(extension).encode("utf-8"))
    return digest.hexdigest()


def _is_local_managed_repository(repository: str) -> bool:
    return repository in {
        LOCAL_IMAGE_REPOSITORY,
        LOCAL_IMAGE_BASE_REPOSITORY,
        DEFAULT_EXTENDED_IMAGE_NAME,
    }
