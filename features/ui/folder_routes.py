"""Create and organize physical folders without switching knowledge areas."""

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import is_linked_vault
from features.ui import folders, selection, workspace


def _open_native_folder(target: Path) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
        return
    if sys.platform == "win32":
        opener = getattr(os, "startfile", None)
        if callable(opener):
            opener(str(target))
            return
    subprocess.Popen(["xdg-open", str(target)])


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
            area_slug = path.partition("/")[0] if len(active.active_dirs) > 1 else active.knowledge_dir
            if not relative:
                raise HTTPException(status_code=403, detail="Area roots must be deleted through the workspace switcher")
            if is_linked_vault(area_slug, workspace.REPO_ROOT):
                raise HTTPException(status_code=403, detail="Linked folders are read-safe — unlink the folder instead of deleting files on disk.")
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

    @router.post("/api/workspace/reveal-folder")
    async def reveal_folder(request: Request) -> dict[str, object]:
        subfolder = ""
        if "application/json" in request.headers.get("content-type", ""):
            body = await read_payload(request)
            if isinstance(body.get("subfolder"), str):
                subfolder = str(body["subfolder"])
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            base = workspace.resolve_safe_knowledge_dir(active.knowledge_dir, create=True)
            try:
                if subfolder:
                    src_base, rel = selection.folder_source(active, workspace.REPO_ROOT, subfolder)
                    target = folders.resolve_subfolder(src_base, rel) if rel else src_base
                else:
                    target = base
            except (ValueError, TypeError, OSError) as exc:
                raise HTTPException(status_code=400, detail="Invalid folder path") from exc
        if not target.is_dir() or target.is_symlink():
            raise HTTPException(status_code=400, detail="Workspace folder is unavailable")
        try:
            _open_native_folder(target)
        except OSError as exc:
            raise HTTPException(status_code=500, detail="Could not open the folder in the system file manager") from exc
        return {"revealed": True, "path": str(target), "platform": sys.platform}

    @router.post("/api/workspace/sync-folder")
    def sync_folder(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            target = workspace.resolve_safe_knowledge_dir(active.knowledge_dir, create=True)
            return workspace.build_workspace_payload(active, reindex(target))

    return router
