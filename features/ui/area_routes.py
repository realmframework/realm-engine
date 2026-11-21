"""Knowledge-area graph and guarded removal routes."""

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import is_linked_vault, link_folder, pick_native_folder
from features.ui import areas, workspace


def build_router(config: Callable[[], WorkspaceConfig], activate: Callable[[WorkspaceConfig], dict[str, object]], chunks: Callable[[], list[KnowledgeChunk]], ingest: Callable[[Path], list[KnowledgeChunk]]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/workspace")
    def get_workspace(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
            return workspace.build_workspace_payload(config(), chunks())

    @router.post("/api/workspace")
    def update_workspace(payload: WorkspaceConfig, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
            return activate(payload)

    @router.get("/api/guides")
    def api_guides(request: Request, tag: str | None = None) -> list[dict[str, object]]:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
            return workspace.group_chunks_into_guides(chunks(), tag)

    @router.get("/api/graph")
    def graph(request: Request, all_areas: bool = True) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            selected = areas.list_areas(workspace.REPO_ROOT, active.knowledge_dir)
            if not all_areas:
                selected = [a for a in selected if a.name in active.active_dirs]
            return areas.graph_payload(selected, workspace.REPO_ROOT, ingest, excluded_map=active.excluded_subfolders)

    @router.post("/api/workspace/link-folder")
    async def link_existing_folder(request: Request) -> dict[str, object]:
        raw_path = ""
        raw_label = ""
        if "application/json" in request.headers.get("content-type", ""):
            try:
                body = await request.json()
            except ValueError:
                body = {}
            if isinstance(body, dict):
                raw_path = str(body.get("path") or "").strip()
                raw_label = str(body.get("label") or "").strip()
        picked = (
            Path(raw_path).expanduser()
            if raw_path
            else await run_in_threadpool(pick_native_folder, "Choose a local folder to link in REALM")
        )
        if picked is None:
            return {"cancelled": True}
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            try:
                slug, resolved = link_folder(picked, workspace.REPO_ROOT, label=raw_label)
            except (ValueError, OSError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            payload = activate(active.model_copy(update={"knowledge_dir": slug, "active_dirs": [slug]}))
            return {**payload, "cancelled": False, "linked_area": slug, "linked_path": str(resolved)}

    @router.delete("/api/workspace/{folder_name}")
    def delete(folder_name: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if folder_name == "knowledge_base":
                raise HTTPException(status_code=403, detail="The default knowledge_base area cannot be deleted")
            try:
                linked = is_linked_vault(folder_name, workspace.REPO_ROOT)
                if not linked:
                    directory = areas.area_path(folder_name, workspace.REPO_ROOT)
                    if not (directory / areas.AREA_MARKER).is_file():
                        raise ValueError("Only managed custom knowledge areas can be deleted")
                if folder_name in active.active_dirs:
                    remaining = [name for name in active.active_dirs if name != folder_name] or ["knowledge_base"]
                    activate(active.model_copy(update={"knowledge_dir": remaining[0], "active_dirs": remaining}))
                areas.delete_area(folder_name, workspace.REPO_ROOT)
            except (ValueError, OSError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {**workspace.build_workspace_payload(config(), chunks()), "deleted_area": folder_name, "unlinked": linked}

    def _split_folder_target(active: WorkspaceConfig, raw_path: str, explicit_area: str = "") -> tuple[str, str]:
        clean = raw_path.strip().strip("/")
        if not clean:
            raise HTTPException(status_code=400, detail="Provide a subfolder path")
        if explicit_area and explicit_area in active.active_dirs:
            return explicit_area, clean
        if len(active.active_dirs) > 1:
            area, _, rel = clean.partition("/")
            if area not in active.active_dirs or not rel:
                raise HTTPException(status_code=400, detail="Choose a subfolder inside a selected workspace")
            return area, rel
        return active.knowledge_dir, clean

    @router.post("/api/subfolders/unload")
    async def unload_subfolder(request: Request) -> dict[str, object]:
        body = await request.json()
        raw_path = str(body.get("path") or "") if isinstance(body, dict) else ""
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            area, rel = _split_folder_target(active, raw_path)
            updated_map = {k: list(v) for k, v in active.excluded_subfolders.items()}
            items = updated_map.setdefault(area, [])
            if rel not in items:
                items.append(rel)
            items.sort()
            payload = activate(active.model_copy(update={"excluded_subfolders": updated_map}))
            return {**payload, "unloaded": rel, "area": area}

    @router.post("/api/subfolders/reload")
    async def reload_subfolder(request: Request) -> dict[str, object]:
        body = await request.json()
        raw_path = str(body.get("path") or "") if isinstance(body, dict) else ""
        explicit_area = str(body.get("area") or "") if isinstance(body, dict) else ""
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            area, rel = _split_folder_target(active, raw_path, explicit_area)
            updated_map = {k: list(v) for k, v in active.excluded_subfolders.items()}
            updated_map[area] = [p for p in updated_map.get(area, []) if p != rel]
            if not updated_map[area]:
                updated_map.pop(area, None)
            payload = activate(active.model_copy(update={"excluded_subfolders": updated_map}))
            return {**payload, "reloaded": rel, "area": area}

    return router
