"""Pure task CRUD, Kanban reordering, and recurring task transitions."""

from core.work_contracts import (
    PriorityLevel,
    RecurrenceRule,
    TaskSubitem,
    WorkBoardState,
    WorkTask,
)
from features.work_board.store import advance_due_date, done_column_ids, new_id, utc_now


def _normalize_positions(tasks: list[WorkTask], column_id: str) -> list[WorkTask]:
    in_col = sorted((t for t in tasks if t.column_id == column_id), key=lambda t: (t.position, t.created_at))
    pos_map = {t.id: idx for idx, t in enumerate(in_col)}
    return [t.model_copy(update={"position": pos_map[t.id]}) if t.id in pos_map else t for t in tasks]


def _maybe_spawn_recurring(state: WorkBoardState, prev: WorkTask, updated: WorkTask, done_cols: set[str]) -> WorkTask | None:
    if updated.recurrence == "none" or prev.column_id in done_cols or updated.column_id not in done_cols:
        return None
    open_col = next((c.id for c in state.columns if not c.is_done), state.columns[0].id)
    now = utc_now()
    reset_subs = [TaskSubitem(id=new_id("sub"), title=s.title, done=False) for s in updated.subtasks]
    return WorkTask(
        id=new_id("tsk"), title=updated.title, description=updated.description, column_id=open_col,
        project_id=updated.project_id, priority=updated.priority, due_date=advance_due_date(updated.due_date, updated.recurrence),
        scheduled_start=updated.scheduled_start, scheduled_end=updated.scheduled_end, recurrence=updated.recurrence,
        subtasks=reset_subs, tags=list(updated.tags), linked_doc_id=updated.linked_doc_id,
        linked_chat_id=updated.linked_chat_id, position=0, created_at=now, updated_at=now,
    )


def add_task(state: WorkBoardState, title: str, column_id: str = "", project_id: str = "", description: str = "", priority: PriorityLevel = "medium", due_date: str = "", scheduled_start: str = "", scheduled_end: str = "", recurrence: RecurrenceRule = "none", subtasks: list[TaskSubitem] | None = None, tags: list[str] | None = None, linked_doc_id: str = "", linked_chat_id: str = "") -> tuple[WorkBoardState, WorkTask]:
    valid_cols = {c.id for c in state.columns}
    col_id = column_id if column_id in valid_cols else state.columns[0].id
    pos, now, done_cols = sum(1 for t in state.tasks if t.column_id == col_id), utc_now(), done_column_ids(state)
    task = WorkTask(
        id=new_id("tsk"), title=title.strip(), description=description.strip(), column_id=col_id,
        project_id=project_id.strip(), priority=priority, due_date=due_date.strip(),
        scheduled_start=scheduled_start.strip(), scheduled_end=scheduled_end.strip(), recurrence=recurrence,
        subtasks=subtasks or [], tags=[t.strip() for t in (tags or []) if t.strip()][:16],
        linked_doc_id=linked_doc_id.strip(), linked_chat_id=linked_chat_id.strip(),
        position=pos, completed_at=now if col_id in done_cols else "", created_at=now, updated_at=now,
    )
    return state.model_copy(update={"tasks": [*state.tasks, task]}), task


def edit_task(state: WorkBoardState, task_id: str, updates: dict[str, object]) -> tuple[WorkBoardState, WorkTask | None]:
    done_cols, valid_cols, now = done_column_ids(state), {c.id for c in state.columns}, utc_now()
    tasks, found, spawned = [], None, None
    for task in state.tasks:
        if task.id != task_id:
            tasks.append(task)
            continue
        clean = {k: v for k, v in updates.items() if v is not None}
        if "column_id" in clean and str(clean["column_id"]) not in valid_cols:
            raise ValueError("Target column does not exist")
        next_col = str(clean.get("column_id", task.column_id))
        clean["updated_at"] = now
        if next_col in done_cols and task.column_id not in done_cols:
            clean["completed_at"] = now
        elif next_col not in done_cols and task.column_id in done_cols:
            clean["completed_at"] = ""
        found = task.model_copy(update=clean)
        spawned = _maybe_spawn_recurring(state, task, found, done_cols)
        tasks.append(found)
    if not found:
        return state, None
    if spawned:
        tasks.append(spawned)
        tasks = _normalize_positions(tasks, spawned.column_id)
    return state.model_copy(update={"tasks": _normalize_positions(tasks, found.column_id)}), found


def remove_task(state: WorkBoardState, task_id: str) -> tuple[WorkBoardState, bool]:
    kept = [t for t in state.tasks if t.id != task_id]
    return (state.model_copy(update={"tasks": kept}), True) if len(kept) != len(state.tasks) else (state, False)


def reorder_task(state: WorkBoardState, task_id: str, target_column_id: str, target_index: int) -> tuple[WorkBoardState, WorkTask | None]:
    if target_column_id not in {c.id for c in state.columns}:
        raise ValueError("Target column does not exist")
    target = next((t for t in state.tasks if t.id == task_id), None)
    if not target:
        return state, None
    done_cols, now = done_column_ids(state), utc_now()
    completed = now if target_column_id in done_cols and target.column_id not in done_cols else ("" if target_column_id not in done_cols else target.completed_at)
    moved = target.model_copy(update={"column_id": target_column_id, "completed_at": completed, "updated_at": now})
    others = [t for t in state.tasks if t.id != task_id]
    dest = sorted((t for t in others if t.column_id == target_column_id), key=lambda t: (t.position, t.created_at))
    dest.insert(max(0, min(target_index, len(dest))), moved)
    pos_map = {t.id: i for i, t in enumerate(dest)}
    rebuilt = [t for t in others if t.column_id != target_column_id] + [t.model_copy(update={"position": pos_map[t.id]}) for t in dest]
    spawned = _maybe_spawn_recurring(state, target, moved, done_cols)
    if spawned:
        rebuilt.append(spawned)
        rebuilt = _normalize_positions(rebuilt, spawned.column_id)
    rebuilt = _normalize_positions(rebuilt, target.column_id)
    return state.model_copy(update={"tasks": rebuilt}), next(t for t in rebuilt if t.id == task_id)
