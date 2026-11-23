"""File rename, file duplicate, and subfolder rename routes for the Explorer."""

import re
import shutil
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.file_types import SUPPORTED_EXTENSIONS
from core.linked_vaults import is_linked_vault
from features.ui import folders, route_helpers, selection, workspace

_SAFE_FILE_RE = re.compile(r"^[\w][\w .()-]{0,95}$")
_SAFE_FOLDER_RE = re.compile(r"^[\w][\w .-]{0,63}$")


def _clean_filename(raw_name: str, fallback_ext: str) -> str:
    name = raw_name.strip()
    if not name or "/" in name or "\\" in name or name.startswith(".") or name.endswith((".", " ")):
        raise ValueError("Use a valid filename without slashes or leading/trailing dots")
    if "." not in name:
        name += fallback_ext
    if not _SAFE_FILE_RE.fullmatch(name):
        raise ValueError("Filename contains unsupported characters")
    if Path(name).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {Path(name).suffix}")
    return name


def _unique_copy_path(source: Path) -> Path:
    stem, ext = source.stem, source.suffix
    for suffix in ("-copy", *(f"-copy-{i}" for i in range(2, 500))):
        cand = source.parent / f"{stem}{suffix}{ext}"
        if not cand.exists() and not cand.is_symlink():
            return cand
    raise ValueError("Too many copies of this file exist in the folder")


def _guide_by_path(chunks: list[KnowledgeChunk], path: Path) -> dict[str, object] | None:
    resolved = path.resolve()
    return next((g for g in workspace.group_chunks_into_guides(chunks) if (fp := str(g.get("file_path") or "")) and Path(fp).resolve() == resolved), None)


def _writable_guide(active: WorkspaceConfig, request: Request, doc_id: str, action: str) -> tuple[str, Path, Path]:
    workspace.require_area(request, active)
    area_slug = route_helpers.guide_area_slug(active, doc_id)
    if is_linked_vault(area_slug, workspace.REPO_ROOT):
        raise HTTPException(status_code=403, detail=f"Linked folders are read-safe — {action} files directly in your folder.")
    base, local_id = workspace.resolve_selected_guide(active, doc_id)
    selection.assert_guide_not_excluded(active, area_slug, local_id)
    source = workspace.resolve_guide_file(base, local_id)
    if source.is_symlink():
        raise HTTPException(status_code=400, detail=f"Symbolic links cannot be {action}d")
    return area_slug, base, source


def _guide_payload(active: WorkspaceConfig, area_slug: str, base: Path, path: Path, chunks: list[KnowledgeChunk]) -> dict[str, object]:
    guide = _guide_by_path(chunks, path)
    new_id = str(guide["doc_id"]) if guide else selection.document_id(active, area_slug, path.relative_to(base).with_suffix("").as_posix())
    return {**workspace.build_workspace_payload(active, chunks), "doc_id": new_id, "filename": path.name, "guide": guide}


def build_router(config: Callable[[], WorkspaceConfig], reindex: Callable[[Path], list[KnowledgeChunk]]) -> APIRouter:
    router = APIRouter()

    @router.post("/api/guides/{doc_id:path}/rename")
    async def rename_guide(doc_id: str, request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        raw_name = body.get("new_name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise HTTPException(status_code=422, detail="Provide a new filename")

        def _rename() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                area_slug, base, source = _writable_guide(active, request, doc_id, "rename")
                try:
                    clean = _clean_filename(raw_name, source.suffix)
                    dest = folders.contained_path(base, (source.parent / clean).relative_to(base).as_posix())
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                if dest.is_symlink() or (dest.name.lower() != source.name.lower() and dest.exists()):
                    raise HTTPException(status_code=409, detail="A file with that name already exists in this folder")
                if dest != source:
                    source.rename(dest)
                return _guide_payload(active, area_slug, base, dest, reindex(base))

        return await run_in_threadpool(_rename)

    @router.post("/api/guides/{doc_id:path}/duplicate")
    async def duplicate_guide(doc_id: str, request: Request) -> dict[str, object]:
        def _duplicate() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                area_slug, base, source = _writable_guide(active, request, doc_id, "duplicate")
                try:
                    dest = _unique_copy_path(source)
                    shutil.copy2(source, dest)
                except (ValueError, OSError) as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                return _guide_payload(active, area_slug, base, dest, reindex(base))

        return await run_in_threadpool(_duplicate)

    @router.post("/api/subfolders/rename")
    async def rename_subfolder(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        path, raw_name = body.get("path"), body.get("new_name")
        if not isinstance(path, str) or not path.strip():
            raise HTTPException(status_code=403, detail="The knowledge area root cannot be renamed as a subfolder")
        if not isinstance(raw_name, str) or not _SAFE_FOLDER_RE.fullmatch(raw_name.strip()):
            raise HTTPException(status_code=400, detail="Use valid folder names with letters, numbers, spaces, underscores or hyphens")
        clean_name = raw_name.strip()

        def _rename_dir() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                base, relative = selection.folder_source(active, workspace.REPO_ROOT, path)
                area_slug = path.partition("/")[0] if len(active.active_dirs) > 1 else active.knowledge_dir
                if not relative:
                    raise HTTPException(status_code=403, detail="Area roots cannot be renamed as a subfolder")
                if is_linked_vault(area_slug, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — rename subfolders directly in your folder.")
                try:
                    target = folders.resolve_subfolder(base, relative)
                    dest = folders.contained_path(base, (target.parent / clean_name).relative_to(base).as_posix())
                except (ValueError, TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                if dest.is_symlink() or (dest.name.lower() != target.name.lower() and dest.exists()):
                    raise HTTPException(status_code=409, detail="A folder with that name already exists")
                if dest != target:
                    target.rename(dest)
                rel_new = dest.relative_to(base).as_posix()
                new_path = f"{area_slug}/{rel_new}" if len(active.active_dirs) > 1 else rel_new
                return {**workspace.build_workspace_payload(active, reindex(base)), "old_path": path, "new_path": new_path}

        return await run_in_threadpool(_rename_dir)

    return router
