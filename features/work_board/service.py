"""Pure CRUD operations for Projects, Kanban Columns, Calendar Events, and Task re-exports."""

from pathlib import Path

from core.json_store import store_lock, validate_iso_date
from core.work_contracts import (
    BoardColumn,
    CalendarEvent,
    EventKind,
    ProjectStatus,
    WorkBoardState,
    WorkProject,
)
from features.work_board import store
from features.work_board.extractor import extract_tasks_deterministic
from features.work_board.task_ops import add_task, edit_task, remove_task, reorder_task

__all__ = [
    "add_column", "add_event", "add_project", "add_task", "add_tasks_from_text", "edit_column", "edit_event", "edit_project", "edit_task",
    "open_task_summaries", "project_name_map", "remove_column", "remove_event", "remove_project", "remove_task", "reorder_task", "schedule_focus_events",
]


def _clean_patch(updates: dict[str, object]) -> dict[str, object]:
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in updates.items() if v is not None}


def add_project(state: WorkBoardState, title: str, description: str = "", color: str = "#4BB8E8", status: ProjectStatus = "active", target_date: str = "", target_hours: float = 0.0) -> tuple[WorkBoardState, WorkProject]:
    dt = validate_iso_date(target_date, allow_empty=True, field_name="target_date")
    proj = WorkProject(id=store.new_id("prj"), title=title.strip(), description=description.strip(), color=color, status=status, target_date=dt, target_hours=max(0.0, float(target_hours)), created_at=store.utc_now())
    return state.model_copy(update={"projects": [*state.projects, proj]}), proj


def edit_project(state: WorkBoardState, project_id: str, updates: dict[str, object]) -> tuple[WorkBoardState, WorkProject | None]:
    clean = _clean_patch(updates)
    if "target_date" in clean:
        clean["target_date"] = validate_iso_date(str(clean["target_date"]), allow_empty=True, field_name="target_date")
    items, found = [], None
    for proj in state.projects:
        if proj.id == project_id:
            found = WorkProject.model_validate({**proj.model_dump(), **clean})
            items.append(found)
        else:
            items.append(proj)
    return (state.model_copy(update={"projects": items}), found) if found else (state, None)


def remove_project(state: WorkBoardState, project_id: str) -> tuple[WorkBoardState, bool]:
    kept = [p for p in state.projects if p.id != project_id]
    if len(kept) == len(state.projects):
        return state, False
    tasks = [t.model_copy(update={"project_id": ""}) if t.project_id == project_id else t for t in state.tasks]
    events = [e.model_copy(update={"project_id": ""}) if e.project_id == project_id else e for e in state.events]
    return state.model_copy(update={"projects": kept, "tasks": tasks, "events": events}), True


def add_column(state: WorkBoardState, title: str, color: str = "#4BB8E8", is_done: bool = False) -> tuple[WorkBoardState, BoardColumn]:
    col = BoardColumn(id=store.new_id("col"), title=title.strip(), color=color, is_done=is_done)
    return state.model_copy(update={"columns": [*state.columns, col]}), col


def edit_column(state: WorkBoardState, column_id: str, updates: dict[str, object]) -> tuple[WorkBoardState, BoardColumn | None]:
    clean = _clean_patch(updates)
    cols, found = [], None
    for col in state.columns:
        if col.id == column_id:
            found = BoardColumn.model_validate({**col.model_dump(), **clean})
            cols.append(found)
        else:
            cols.append(col)
    return (state.model_copy(update={"columns": cols}), found) if found else (state, None)


def remove_column(state: WorkBoardState, column_id: str) -> tuple[WorkBoardState, bool]:
    if len(state.columns) <= 1:
        raise ValueError("Keep at least one Kanban column")
    kept = [c for c in state.columns if c.id != column_id]
    if len(kept) == len(state.columns):
        return state, False
    fallback_id = kept[0].id
    tasks = [t.model_copy(update={"column_id": fallback_id}) if t.column_id == column_id else t for t in state.tasks]
    return state.model_copy(update={"columns": kept, "tasks": tasks}), True


def add_event(state: WorkBoardState, title: str, date_str: str, start_time: str = "", end_time: str = "", kind: EventKind = "event", notes: str = "", project_id: str = "", task_id: str = "", uid: str = "") -> tuple[WorkBoardState, CalendarEvent]:
    dt, eid = validate_iso_date(date_str, allow_empty=False, field_name="date"), store.new_id("evt")
    ev = CalendarEvent(id=eid, title=title.strip(), notes=notes.strip(), kind=kind, date=dt, start_time=start_time.strip(), end_time=end_time.strip(), project_id=project_id.strip(), task_id=task_id.strip(), uid=uid.strip() or f"{eid}@realm-engine.local")
    return state.model_copy(update={"events": [*state.events, ev]}), ev


def edit_event(state: WorkBoardState, event_id: str, updates: dict[str, object]) -> tuple[WorkBoardState, CalendarEvent | None]:
    clean = _clean_patch(updates)
    if "date" in clean:
        clean["date"] = validate_iso_date(str(clean["date"]), allow_empty=False, field_name="date")
    items, found = [], None
    for ev in state.events:
        if ev.id == event_id:
            found = CalendarEvent.model_validate({**ev.model_dump(), **clean})
            items.append(found)
        else:
            items.append(ev)
    return (state.model_copy(update={"events": items}), found) if found else (state, None)


def remove_event(state: WorkBoardState, event_id: str) -> tuple[WorkBoardState, bool]:
    kept = [e for e in state.events if e.id != event_id]
    return (state.model_copy(update={"events": kept}), True) if len(kept) != len(state.events) else (state, False)


def project_name_map(area: str, root: Path | None = None) -> dict[str, str]:
    path = store.board_path(area, root)
    with store_lock(path):
        return {p.id: p.title for p in store.load_board(path).projects}


def open_task_summaries(area: str, root: Path | None = None) -> list[dict[str, str]]:
    path = store.board_path(area, root)
    with store_lock(path):
        state = store.load_board(path)
        done_cols = store.done_column_ids(state)
        return [{"id": t.id, "title": t.title, "project_id": t.project_id, "due_date": t.due_date, "priority": t.priority} for t in state.tasks if t.column_id not in done_cols][:25]


def schedule_focus_events(area: str, blocks: list[object], root: Path | None = None) -> int:
    path = store.board_path(area, root)
    with store_lock(path):
        state, added = store.load_board(path), 0
        for blk in blocks:
            title, dt = str(getattr(blk, "title", "")).strip(), str(getattr(blk, "date", "")).strip()
            if not title or not dt:
                continue
            state, _ = add_event(state, title, dt, str(getattr(blk, "start_time", "")), str(getattr(blk, "end_time", "")), "focus", str(getattr(blk, "notes", "")), str(getattr(blk, "project_id", "")))
            added += 1
        if added:
            store.save_board(state, path)
        return added


def add_tasks_from_text(area: str, text: str, project_id: str = "", root: Path | None = None) -> int:
    items = extract_tasks_deterministic(text, max_items=8)
    if not items:
        return 0
    path = store.board_path(area, root)
    with store_lock(path):
        state = store.load_board(path)
        for item in items:
            state, _ = add_task(state, item["title"], project_id=project_id, due_date=item.get("due_date", ""), priority=item.get("priority", "medium"))  # type: ignore[arg-type]
        store.save_board(state, path)
        return len(items)
