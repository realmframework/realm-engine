"""Atomic local persistence, date arithmetic, summary metrics, and RAG snapshot for Work Board."""

import calendar
from datetime import date, timedelta
from pathlib import Path

from core.json_store import (
    area_store_path,
    load_model_json,
    new_id,
    save_model_json,
    store_lock,
    today_iso,
    utc_now,
)
from core.work_contracts import BoardColumn, RecurrenceRule, WorkBoardState

__all__ = [
    "advance_due_date",
    "board_path",
    "board_summary",
    "default_columns",
    "done_column_ids",
    "load_board",
    "new_id",
    "render_board_markdown",
    "save_board",
    "store_lock",
    "today_iso",
    "utc_now",
]


def default_columns() -> list[BoardColumn]:
    return [
        BoardColumn(id="todo", title="To Do", color="#4BB8E8", is_done=False),
        BoardColumn(id="doing", title="In Progress", color="#A78BFA", is_done=False),
        BoardColumn(id="review", title="Review", color="#F59E0B", is_done=False),
        BoardColumn(id="done", title="Done", color="#38D399", is_done=True),
    ]


def board_path(area: str, root: Path | None = None) -> Path:
    return area_store_path(area, "work_board.json", root)


def load_board(path: Path) -> WorkBoardState:
    state = load_model_json(path, WorkBoardState, lambda: WorkBoardState(columns=default_columns()))
    return state if state.columns else state.model_copy(update={"columns": default_columns()})


def save_board(state: WorkBoardState, path: Path) -> WorkBoardState:
    normalized = state if state.columns else state.model_copy(update={"columns": default_columns()})
    return save_model_json(normalized, path, WorkBoardState)


def advance_due_date(iso_date: str, recurrence: RecurrenceRule) -> str:
    if recurrence == "none":
        return ""
    try:
        base = date.fromisoformat(iso_date) if iso_date else date.today()
    except ValueError:
        base = date.today()
    if recurrence == "daily":
        return (base + timedelta(days=1)).isoformat()
    if recurrence == "weekly":
        return (base + timedelta(days=7)).isoformat()
    next_month = 1 if base.month == 12 else base.month + 1
    next_year = base.year + (1 if base.month == 12 else 0)
    return date(next_year, next_month, min(base.day, calendar.monthrange(next_year, next_month)[1])).isoformat()


def done_column_ids(state: WorkBoardState) -> set[str]:
    return {col.id for col in state.columns if col.is_done}


def board_summary(state: WorkBoardState, today: str | None = None) -> dict[str, int]:
    ref, done_cols = today or today_iso(), done_column_ids(state)
    open_tasks = [t for t in state.tasks if t.column_id not in done_cols]
    return {
        "open_tasks": len(open_tasks),
        "done_tasks": len(state.tasks) - len(open_tasks),
        "today_tasks": sum(1 for t in open_tasks if t.due_date == ref),
        "overdue_tasks": sum(1 for t in open_tasks if t.due_date and t.due_date < ref),
        "upcoming_tasks": sum(1 for t in open_tasks if t.due_date and t.due_date > ref),
        "projects_active": sum(1 for p in state.projects if p.status == "active"),
        "events_upcoming": sum(1 for e in state.events if e.date >= ref),
    }


def render_board_markdown(state: WorkBoardState, workspace_title: str = "Workspace") -> str:
    lines = ["---", f"title: {workspace_title} — Projects, Tasks & Calendar", "tags: [work-board, projects, tasks, calendar]", "---", f"# {workspace_title} — Projects, Tasks & Calendar", ""]
    if state.projects:
        lines.append("## Active Projects")
        for p in state.projects:
            meta = [p.status, *([f"target {p.target_date}"] if p.target_date else []), *([f"{p.target_hours:g}h budget"] if p.target_hours > 0 else [])]
            lines.append(f"- **{p.title}** ({', '.join(meta)}){': ' + p.description if p.description else ''}")
        lines.append("")
    proj_names = {p.id: p.title for p in state.projects}
    for col in state.columns:
        col_tasks = sorted((t for t in state.tasks if t.column_id == col.id), key=lambda t: (t.position, t.created_at))
        if not col_tasks:
            continue
        lines.append(f"## {col.title}")
        for task in col_tasks:
            mark = "x" if col.is_done else " "
            parts = [f"priority: {task.priority}", *([f"due: {task.due_date}"] if task.due_date else []), *([f"project: {proj_names[task.project_id]}"] if task.project_id in proj_names else [])]
            lines.append(f"- [{mark}] **{task.title}** ({', '.join(parts)})")
            if task.description:
                lines.append(f"  - {task.description.splitlines()[0][:200]}")
        lines.append("")
    if state.events:
        lines.append("## Calendar Schedule")
        for ev in sorted(state.events, key=lambda item: (item.date, item.start_time)):
            slot = f" {ev.start_time}-{ev.end_time}" if ev.start_time and ev.end_time else (f" {ev.start_time}" if ev.start_time else "")
            lines.append(f"- **{ev.date}{slot}** [{ev.kind}] {ev.title}{(' — ' + ev.notes[:140]) if ev.notes else ''}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"
