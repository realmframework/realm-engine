"""Knowledge-area graph and guarded removal routes."""

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from core.contracts import KnowledgeChunk, WorkspaceConfig
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
            return areas.graph_payload(selected, workspace.REPO_ROOT, ingest)

    @router.delete("/api/workspace/{folder_name}")
    def delete(folder_name: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if folder_name == "knowledge_base":
                raise HTTPException(status_code=403, detail="The default knowledge_base area cannot be deleted")
            try:
                directory = areas.area_path(folder_name, workspace.REPO_ROOT)
                if not (directory / areas.AREA_MARKER).is_file():
                    raise ValueError("Only managed custom knowledge areas can be deleted")
                if folder_name in active.active_dirs:
                    remaining = [name for name in active.active_dirs if name != folder_name] or ["knowledge_base"]
                    activate(active.model_copy(update={"knowledge_dir": remaining[0], "active_dirs": remaining}))
                areas.delete_area(folder_name, workspace.REPO_ROOT)
            except (ValueError, OSError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {**workspace.build_workspace_payload(config(), chunks()), "deleted_area": folder_name}

    return router
