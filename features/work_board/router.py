"""FastAPI router for Projects, Kanban Board, Task Manager, and Local Calendar (.ics)."""

from collections.abc import Callable, Mapping
from pathlib import Path
from threading import RLock
from typing import cast

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from core.contracts import TutorConfig, WorkspaceConfig
from core.work_contracts import PriorityLevel, WorkBoardState
from features.work_board import extractor, ics_codec, payloads, service, store

BOARD_LOCK = RLock()
SourceResolver = Callable[[str, int | None, str, str], str]
SyncVaultFn = Callable[[str, str, str], dict[str, object]]


def _payload(state: WorkBoardState, area: str, extra: Mapping[str, object] | None = None) -> dict[str, object]:
    return {**state.model_dump(), "summary": store.board_summary(state), "area": area, **(extra or {})}


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    resolve_source: SourceResolver,
    stream_messages: extractor.StreamMessagesFn | None = None,
    sync_vault: SyncVaultFn | None = None,
    root_provider: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _area_and_path() -> tuple[WorkspaceConfig, Path]:
        cfg = get_config()
        return cfg, store.board_path(cfg.knowledge_dir, root_provider() if root_provider else None)

    def _mutate(fn: Callable[[WorkBoardState], tuple[WorkBoardState, object]]) -> dict[str, object]:
        with BOARD_LOCK:
            cfg, path = _area_and_path()
            try:
                next_state, item = fn(store.load_board(path))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if item is None or item is False:
                raise HTTPException(status_code=404, detail="Item not found")
            store.save_board(next_state, path)
            extra: dict[str, object] = {"item": item.model_dump()} if isinstance(item, BaseModel) else {"deleted": bool(item)}
            return _payload(next_state, cfg.knowledge_dir, extra)

    @router.get("/api/work-board")
    def get_board() -> dict[str, object]:
        with BOARD_LOCK:
            cfg, path = _area_and_path()
            return _payload(store.load_board(path), cfg.knowledge_dir)
    @router.post("/api/work-board/projects")
    def create_project(body: payloads.ProjectCreateBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_project(s, body.title, body.description, body.color, body.status, body.target_date, body.target_hours))
    @router.patch("/api/work-board/projects/{project_id}")
    def update_project(project_id: str, body: payloads.ProjectPatchBody) -> dict[str, object]:
        return _mutate(lambda s: service.edit_project(s, project_id, body.model_dump(exclude_unset=True)))
    @router.delete("/api/work-board/projects/{project_id}")
    def delete_project(project_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_project(s, project_id))
    @router.post("/api/work-board/columns")
    def create_column(body: payloads.ColumnCreateBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_column(s, body.title, body.color, body.is_done))
    @router.patch("/api/work-board/columns/{column_id}")
    def update_column(column_id: str, body: payloads.ColumnPatchBody) -> dict[str, object]:
        return _mutate(lambda s: service.edit_column(s, column_id, body.model_dump(exclude_unset=True)))
    @router.delete("/api/work-board/columns/{column_id}")
    def delete_column(column_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_column(s, column_id))
    @router.post("/api/work-board/tasks")
    def create_task(body: payloads.TaskCreateBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_task(s, body.title, body.column_id, body.project_id, body.description, body.priority, body.due_date, body.scheduled_start, body.scheduled_end, body.recurrence, body.subtasks, body.tags, body.linked_doc_id, body.linked_chat_id))
    @router.patch("/api/work-board/tasks/{task_id}")
    def update_task(task_id: str, body: payloads.TaskPatchBody) -> dict[str, object]:
        return _mutate(lambda s: service.edit_task(s, task_id, body.model_dump(exclude_unset=True)))
    @router.delete("/api/work-board/tasks/{task_id}")
    def delete_task(task_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_task(s, task_id))
    @router.post("/api/work-board/tasks/reorder")
    def reorder_task(body: payloads.TaskReorderBody) -> dict[str, object]:
        return _mutate(lambda s: service.reorder_task(s, body.task_id, body.target_column_id, body.target_index))
    @router.post("/api/work-board/events")
    def create_event(body: payloads.EventCreateBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_event(s, body.title, body.date, body.start_time, body.end_time, body.kind, body.notes, body.project_id, body.task_id))
    @router.patch("/api/work-board/events/{event_id}")
    def update_event(event_id: str, body: payloads.EventPatchBody) -> dict[str, object]:
        return _mutate(lambda s: service.edit_event(s, event_id, body.model_dump(exclude_unset=True)))
    @router.delete("/api/work-board/events/{event_id}")
    def delete_event(event_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_event(s, event_id))

    @router.post("/api/work-board/extract")
    async def extract_tasks(body: payloads.ExtractTasksBody, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        cfg = get_config()
        source_text = resolve_source(body.chat_id, body.turn_index, body.doc_id, body.text)
        if not source_text.strip():
            raise HTTPException(status_code=400, detail="Provide text, a chat turn, or a guide to extract tasks from.")
        can_ai = body.use_ai and stream_messages is not None and not (cfg.strict_local_only and body.provider != "ollama")
        tutor_cfg = TutorConfig(provider=body.provider, model=body.model, api_key=x_api_key or None, temperature=0.1) if can_ai else None
        drafts, mode = await extractor.extract_tasks_with_ai(source_text, stream_messages if can_ai else None, tutor_cfg, language=body.language)
        with BOARD_LOCK:
            _, path = _area_and_path()
            state = store.load_board(path)
            if not body.save or not drafts:
                return _payload(state, cfg.knowledge_dir, {"extracted": drafts, "mode": mode, "created_count": 0})
            created = []
            for item in drafts:
                prio = cast(PriorityLevel, item["priority"] if item["priority"] in {"low", "medium", "high", "urgent"} else "medium")
                state, task = service.add_task(state, item["title"], body.column_id, body.project_id, item["description"], prio, item["due_date"], linked_doc_id=body.doc_id, linked_chat_id=body.chat_id)
                created.append(task.model_dump())
            store.save_board(state, path)
            return _payload(state, cfg.knowledge_dir, {"extracted": created, "mode": mode, "created_count": len(created)})

    @router.post("/api/work-board/sync-vault")
    def sync_board_to_vault() -> dict[str, object]:
        if sync_vault is None:
            raise HTTPException(status_code=501, detail="Vault sync is not configured.")
        with BOARD_LOCK:
            cfg, path = _area_and_path()
            if not cfg.knowledge_dir:
                raise HTTPException(status_code=400, detail="Select or create a workspace before syncing to Library.")
            markdown = store.render_board_markdown(store.load_board(path), cfg.app_title or cfg.knowledge_dir)
        return sync_vault(cfg.knowledge_dir, "work_board_snapshot.md", markdown)

    @router.get("/api/work-board/calendar.ics")
    def download_ics() -> Response:
        with BOARD_LOCK:
            cfg, path = _area_and_path()
            ics_text = ics_codec.export_ics(store.load_board(path), cfg.app_title or "REALM Engine")
        safe_name = (cfg.knowledge_dir or "realm").replace('"', "")
        return Response(content=ics_text.encode("utf-8"), media_type="text/calendar; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{safe_name}_calendar.ics"', "Cache-Control": "no-store"})

    @router.post("/api/work-board/calendar/import-ics")
    def upload_ics(body: payloads.ImportIcsBody) -> dict[str, object]:
        with BOARD_LOCK:
            cfg, path = _area_and_path()
            state = store.load_board(path)
            imported = ics_codec.import_ics(body.ics_text, {e.uid for e in state.events if e.uid})
            if imported:
                state = state.model_copy(update={"events": [*state.events, *imported]})
                store.save_board(state, path)
            return _payload(state, cfg.knowledge_dir, {"imported_count": len(imported)})

    return router
