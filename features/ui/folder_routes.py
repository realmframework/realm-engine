"""Create and organize physical folders without switching knowledge areas."""

import os
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import is_linked_vault
from features.ui import folders, route_helpers, selection, workspace


def _open_native_folder(target: Path) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    elif sys.platform == "win32" and callable(opener := getattr(os, "startfile", None)):
        opener(str(target))
    else:
        subprocess.Popen(["xdg-open", str(target)])

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
        payload = await route_helpers.read_json_dict(request)

        def _create() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                try:
                    name = payload.get("name")
                    if not isinstance(name, str):
                        raise TypeError("Provide a subfolder path")
                    area_slug = name.partition("/")[0] if len(active.active_dirs) > 1 else active.knowledge_dir
                    if is_linked_vault(area_slug, workspace.REPO_ROOT):
                        raise HTTPException(status_code=403, detail="Linked folders are read-safe — create subfolders directly in your external folder.")
                    base, name = selection.folder_source(active, workspace.REPO_ROOT, name)
                    target = folders.resolve_subfolder(base, name, create=True)
                except (ValueError, TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid subfolder path") from exc
                return {"created": (area_slug + "/" if len(active.active_dirs) > 1 else "") + target.relative_to(base).as_posix(), "subfolders": selection.subfolders(active, workspace.REPO_ROOT)}

        return await run_in_threadpool(_create)

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
        payload = await route_helpers.read_json_dict(request)

        def _move() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                area_slug = doc_id.split("::", 1)[0] if len(active.active_dirs) > 1 and "::" in doc_id else active.knowledge_dir
                if is_linked_vault(area_slug, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — move files directly in your external folder.")
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
                new_id = selection.document_id(active, area_slug, target.relative_to(base).with_suffix("").as_posix())
                chunks = reindex(base)
                return {**workspace.build_workspace_payload(active, chunks), "doc_id": new_id, "guide": next((g for g in workspace.group_chunks_into_guides(chunks) if g["doc_id"] == new_id), None)}

        return await run_in_threadpool(_move)

    @router.post("/api/workspace/reveal-folder")
    async def reveal_folder(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, required=False)
        subfolder = str(body["subfolder"]) if isinstance(body.get("subfolder"), str) else ""

        def _reveal() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                base = workspace.resolve_safe_knowledge_dir(active.knowledge_dir, create=True) if active.knowledge_dir else workspace.REPO_ROOT
                try:
                    target = folders.resolve_subfolder(*(selection.folder_source(active, workspace.REPO_ROOT, subfolder))) if subfolder else base
                except (ValueError, TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Invalid folder path") from exc
            if not target.is_dir() or target.is_symlink():
                raise HTTPException(status_code=400, detail="Workspace folder is unavailable")
            try:
                _open_native_folder(target)
            except OSError as exc:
                raise HTTPException(status_code=500, detail="Could not open the folder in the system file manager") from exc
            return {"revealed": True, "path": str(target), "platform": sys.platform}

        return await run_in_threadpool(_reveal)

    @router.post("/api/workspace/sync-folder")
    def sync_folder(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            return workspace.build_workspace_payload(active, reindex(workspace.resolve_safe_knowledge_dir(active.knowledge_dir, create=True)) if active.knowledge_dir else [])

    return router
