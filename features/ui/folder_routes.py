"""Create and organize physical folders without switching knowledge areas."""

import shutil
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from core.contracts import KnowledgeChunk, WorkspaceConfig
from features.ui import folders, selection, workspace


async def read_payload(request: Request) -> dict[str, object]:
    try:
        payload = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Provide a JSON object") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Provide a JSON object")
    return payload


def build_router(config: Callable[[], WorkspaceConfig], reindex: Callable[[Path], list[KnowledgeChunk]]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/subfolders")
    def catalog(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            return {"subfolders": selection.subfolders(active, workspace.REPO_ROOT)}

    @router.post("/api/subfolders")
    async def create(request: Request) -> dict[str, object]:
        payload = await read_payload(request)
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            try:
                name = payload.get("name")
                if not isinstance(name, str):
                    raise TypeError("Provide a subfolder path")
                base, name = selection.folder_source(active, workspace.REPO_ROOT, name)
                target = folders.resolve_subfolder(base, name, create=True)
            except (ValueError, TypeError, OSError) as exc:
                raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
            return {"created": (base.name + "/" if len(active.active_dirs) > 1 else "") + target.relative_to(base).as_posix(), "subfolders": selection.subfolders(active, workspace.REPO_ROOT)}

    @router.delete("/api/subfolders")
    def delete(request: Request, path: str) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not path:
                raise HTTPException(status_code=403, detail="The knowledge area root cannot be deleted as a subfolder")
            base, relative = selection.folder_source(active, workspace.REPO_ROOT, path)
            if not relative:
                raise HTTPException(status_code=403, detail="Area roots must be deleted through the workspace switcher")
            try:
                target = folders.resolve_subfolder(base, relative)
            except (ValueError, TypeError, OSError) as exc:
                raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
            try:
                shutil.rmtree(target)
            except OSError as exc:
                reindex(base)
                raise HTTPException(status_code=400, detail="Some files could not be removed. Refresh Library to review the remaining files.") from exc
            return {**workspace.build_workspace_payload(active, reindex(base)), "deleted": path}

    @router.post("/api/guides/{doc_id:path}/move")
    async def move(doc_id: str, request: Request) -> dict[str, object]:
        payload = await read_payload(request)
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            base, local_id = workspace.resolve_selected_guide(active, doc_id)
            source = workspace.resolve_guide_file(base, local_id)
            try:
                name = payload.get("subfolder")
                if len(active.active_dirs) > 1 and isinstance(name, str) and name.split("/")[0] in active.active_dirs:
                    destination, name = selection.folder_source(active, workspace.REPO_ROOT, name)
                    if destination != base:
                        raise ValueError("Moves must stay in the guide's source area")
                target = folders.resolve_subfolder(base, name, create=True) / source.name
                if target.is_symlink() or target != source and target.exists():
                    raise HTTPException(status_code=409, detail="A guide with that filename already exists in this subfolder")
                if target != source:
                    source.rename(target)
            except (ValueError, TypeError, OSError) as exc:
                raise HTTPException(status_code=400, detail="Unable to move this guide to the selected subfolder") from exc
            new_id = selection.document_id(active, base.name, target.relative_to(base).with_suffix("").as_posix())
            chunks = reindex(base)
            guide = next(guide for guide in workspace.group_chunks_into_guides(chunks) if guide["doc_id"] == new_id)
            return {**workspace.build_workspace_payload(active, chunks), "doc_id": new_id, "guide": guide}

    return router
