"""Knowledge-area graph and guarded removal routes."""

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import is_linked_vault, link_folder, pick_native_folder
from features.ui import areas, workflow_routes, workspace


async def _json_dict(request: Request, *, required: bool = True) -> dict[str, object]:
    if not required and "application/json" not in request.headers.get("content-type", ""):
        return {}
    try:
        body = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Provide valid JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Provide a JSON object")
    return body


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
        body = await _json_dict(request, required=False)
        raw_path, raw_label = str(body.get("path") or "").strip(), str(body.get("label") or "").strip()
        picked = Path(raw_path).expanduser() if raw_path else await run_in_threadpool(pick_native_folder, "Choose a local folder to link in REALM")
        if picked is None:
            return {"cancelled": True}

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                try:
                    slug, resolved = link_folder(picked, workspace.REPO_ROOT, label=raw_label)
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                except OSError as exc:
                    raise HTTPException(status_code=400, detail="Could not link the selected folder") from exc
                return {**activate(active.model_copy(update={"knowledge_dir": slug, "active_dirs": [slug]})), "cancelled": False, "linked_area": slug, "linked_path": str(resolved)}
        return await run_in_threadpool(_apply)
    @router.delete("/api/workspace/{folder_name}")
    def delete(folder_name: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            try:
                linked = is_linked_vault(folder_name, workspace.REPO_ROOT)
                if not linked and folder_name != "knowledge_base" and not (areas.area_path(folder_name, workspace.REPO_ROOT) / areas.AREA_MARKER).is_file():
                    raise ValueError("Only managed knowledge areas can be deleted")
                areas.delete_area(folder_name, workspace.REPO_ROOT)
                if folder_name in active.active_dirs:
                    remaining = [n for n in active.active_dirs if n != folder_name] or ([a.name for a in areas.list_areas(workspace.REPO_ROOT, "") if a.name != folder_name][:1])
                    activate(active.model_copy(update={"knowledge_dir": remaining[0] if remaining else "", "active_dirs": remaining}))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            except OSError as exc:
                raise HTTPException(status_code=400, detail="Could not delete workspace area") from exc
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
        raw_path = str((await _json_dict(request)).get("path") or "")

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                area, rel = _split_folder_target(active, raw_path)
                updated_map = {k: list(v) for k, v in active.excluded_subfolders.items()}
                items = updated_map.setdefault(area, [])
                if rel not in items:
                    items.append(rel)
                items.sort()
                return {**activate(active.model_copy(update={"excluded_subfolders": updated_map})), "unloaded": rel, "area": area}

        return await run_in_threadpool(_apply)

    @router.post("/api/subfolders/reload")
    async def reload_subfolder(request: Request) -> dict[str, object]:
        body = await _json_dict(request)
        raw_path, explicit_area = str(body.get("path") or ""), str(body.get("area") or "")

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                area, rel = _split_folder_target(active, raw_path, explicit_area)
                updated_map = {k: list(v) for k, v in active.excluded_subfolders.items()}
                updated_map[area] = [p for p in updated_map.get(area, []) if p != rel]
                if not updated_map[area]:
                    updated_map.pop(area, None)
                return {**activate(active.model_copy(update={"excluded_subfolders": updated_map})), "reloaded": rel, "area": area}

        return await run_in_threadpool(_apply)

    router.include_router(workflow_routes.build_router(config, chunks))
    return router
