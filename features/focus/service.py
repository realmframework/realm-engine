"""Goal Seasons trajectory analytics, Deep Focus session store, and AI/offline Weekly Coach."""

import json
import re
import uuid
from collections.abc import AsyncIterator, Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from core.contracts import TutorConfig
from core.db import atomic_write_text, backup_corrupt_file
from core.impact_contracts import (
    FocusSession,
    FocusState,
    GoalSeason,
    GoalStatus,
    PlannedFocusBlock,
    SoundscapeMode,
)
from core.linked_vaults import CACHE_DIR, cache_study_path
from core.runtime import data_root

StreamMessagesFn = Callable[..., AsyncIterator[dict[str, object]]]

def utc_now() -> str:
    return datetime.now(UTC).isoformat()
def today_iso() -> str:
    return date.today().isoformat()
def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"

def focus_path(area: str, root: Path | None = None) -> Path:
    resolved_root = (root or data_root()).resolve()
    if not area or not area.strip():
        cache = resolved_root / CACHE_DIR
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / "_default.focus_engine.json"
    else:
        target = cache_study_path(area.strip(), "focus_engine.json", resolved_root)
    if target.is_symlink() or target.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Focus storage cannot be a symbolic link")
    return target

def load_focus(path: Path) -> FocusState:
    if path.is_symlink():
        raise ValueError("Focus storage cannot be a symbolic link")
    if not path.is_file():
        return FocusState()
    try:
        return FocusState.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError:
        backup_corrupt_file(path)
        return FocusState()
    except OSError:
        return FocusState()

def save_focus(state: FocusState, path: Path) -> None:
    if path.is_symlink() or path.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Focus storage cannot be a symbolic link")
    atomic_write_text(path, state.model_dump_json(indent=2))

def goal_trajectory(goal: GoalSeason, sessions: list[FocusSession], today: str | None = None) -> dict[str, object]:
    """Compute logged hours, completion %, elapsed season %, and trajectory pace."""
    ref, s_dt, e_dt = (date.fromisoformat(today) if today else date.today()), date.fromisoformat(goal.start_date), date.fromisoformat(goal.end_date)
    total_days = max(1, (e_dt - s_dt).days)
    pct_time = round((max(0, min(total_days, (ref - s_dt).days)) / total_days) * 100.0, 1)
    logged_hrs = round(sum(s.actual_minutes for s in sessions if s.goal_id == goal.id or (goal.project_id and s.project_id == goal.project_id)) / 60.0, 2)
    pct_hours = round(min(100.0, (logged_hrs / max(0.1, goal.target_hours)) * 100.0), 1)
    pace = "ahead" if pct_hours >= pct_time + 8 else ("behind" if pct_time > 10 and pct_hours < pct_time - 10 else "on_track")
    return {"logged_hours": logged_hrs, "pct_hours": pct_hours, "pct_time": pct_time, "pace": pace, "days_left": max(0, (e_dt - ref).days)}

def focus_analytics(state: FocusState, today: str | None = None) -> dict[str, object]:
    ref = date.fromisoformat(today) if today else date.today()
    week_start = (ref - timedelta(days=ref.weekday())).isoformat()
    total_mins = sum(s.actual_minutes for s in state.sessions)
    week_mins = sum(s.actual_minutes for s in state.sessions if s.date >= week_start)
    avg_q = round(sum(s.quality_rating for s in state.sessions) / len(state.sessions), 2) if state.sessions else 0.0
    days_with_focus, streak, cursor = {s.date for s in state.sessions}, 0, ref
    while cursor.isoformat() in days_with_focus:
        streak, cursor = streak + 1, cursor - timedelta(days=1)
    return {
        "total_hours": round(total_mins / 60.0, 2), "week_hours": round(week_mins / 60.0, 2),
        "session_count": len(state.sessions), "avg_quality": avg_q, "streak_days": streak,
        "trajectories": {g.id: goal_trajectory(g, state.sessions, ref.isoformat()) for g in state.goals},
    }

def add_goal(state: FocusState, title: str, why: str = "", project_id: str = "", start_date: str = "", end_date: str = "", target_hours: float = 24.0, weekly_milestones: list[str] | None = None, status: GoalStatus = "active") -> tuple[FocusState, GoalSeason]:
    s_date = start_date.strip() or today_iso()
    e_date = end_date.strip() or (date.fromisoformat(s_date) + timedelta(days=84)).isoformat()
    goal = GoalSeason(id=new_id("gol"), title=title.strip(), why=why.strip(), project_id=project_id.strip(), start_date=s_date, end_date=e_date, target_hours=max(1.0, float(target_hours)), weekly_milestones=[m.strip() for m in (weekly_milestones or []) if m.strip()][:24], status=status, created_at=utc_now())
    return state.model_copy(update={"goals": [*state.goals, goal]}), goal

def edit_goal(state: FocusState, goal_id: str, updates: dict[str, object]) -> tuple[FocusState, GoalSeason | None]:
    items, found = [], None
    for g in state.goals:
        if g.id == goal_id:
            found = g.model_copy(update={k: v for k, v in updates.items() if v is not None})
            items.append(found)
        else:
            items.append(g)
    return (state.model_copy(update={"goals": items}), found) if found else (state, None)

def remove_goal(state: FocusState, goal_id: str) -> tuple[FocusState, bool]:
    kept = [g for g in state.goals if g.id != goal_id]
    return (state.model_copy(update={"goals": kept}), True) if len(kept) != len(state.goals) else (state, False)

def add_session(state: FocusState, label: str, planned_minutes: int, actual_minutes: float, quality_rating: int = 4, soundscape: SoundscapeMode = "off", reflection: str = "", goal_id: str = "", project_id: str = "", task_id: str = "", date_str: str = "") -> tuple[FocusState, FocusSession]:
    sess = FocusSession(id=new_id("foc"), date=date_str.strip() or today_iso(), goal_id=goal_id.strip(), project_id=project_id.strip(), task_id=task_id.strip(), label=label.strip(), planned_minutes=planned_minutes, actual_minutes=round(float(actual_minutes), 1), quality_rating=quality_rating, soundscape=soundscape, reflection=reflection.strip(), completed_at=utc_now())
    return state.model_copy(update={"sessions": [sess, *state.sessions]}), sess

def remove_session(state: FocusState, session_id: str) -> tuple[FocusState, bool]:
    kept = [s for s in state.sessions if s.id != session_id]
    return (state.model_copy(update={"sessions": kept}), True) if len(kept) != len(state.sessions) else (state, False)

async def generate_weekly_plan(state: FocusState, open_tasks: list[dict[str, str]], stream_messages: StreamMessagesFn | None, tutor_config: TutorConfig | None, *, language: str = "en", start_day: str | None = None) -> tuple[list[PlannedFocusBlock], str]:
    """Propose balanced weekday Deep Focus blocks for active goals & priority tasks."""
    base = date.fromisoformat(start_day) if start_day else date.today()
    weekdays = [base + timedelta(days=i) for i in range(7) if (base + timedelta(days=i)).weekday() < 5][:5]
    active_goals = [g for g in state.goals if g.status == "active"]
    items = [(t.get("title", ""), t.get("project_id", ""), "") for t in open_tasks[:5]] + [(f"Focus: {g.title}", g.project_id, g.id) for g in active_goals[:5]]
    fallback = [PlannedFocusBlock(title=(items[i % len(items)][0] if items else "Deep Focus Session")[:180], date=d.isoformat(), start_time="09:00", end_time="10:30", project_id=items[i % len(items)][1] if items else "", goal_id=items[i % len(items)][2] if items else "", notes="Protected morning deep focus block") for i, d in enumerate(weekdays)]
    if stream_messages is None or tutor_config is None or not items:
        return fallback, "deterministic"
    lang = {"de": "German", "es": "Spanish"}.get(language, "English")
    ctx = f"Dates: {[d.isoformat() for d in weekdays]}\nGoals: {[g.title for g in active_goals[:6]]}\nTasks: {[t.get('title') for t in open_tasks[:8]]}"
    sys_p = f"Create 4-5 realistic 90-minute weekday Deep Focus blocks in {lang}. Reply ONLY with JSON array inside <plan_json>[...]</plan_json> where each item has keys: title, date (YYYY-MM-DD), start_time (HH:MM), end_time (HH:MM), notes."
    buf: list[str] = []
    try:
        async for ev in stream_messages([{"role": "system", "content": sys_p}, {"role": "user", "content": ctx}], tutor_config):
            if ev.get("event") == "token":
                buf.append(str(ev.get("text") or ""))
    except Exception:
        return fallback, "deterministic"
    raw = "".join(buf)
    m = re.search(r"<plan_json>\s*(\[.*?\])\s*</plan_json>", raw, re.DOTALL)
    try:
        parsed = json.loads(m.group(1) if m else raw[raw.find("[") : raw.rfind("]") + 1])
        blocks = [PlannedFocusBlock.model_validate(b) for b in parsed[:7] if isinstance(b, dict)]
        if blocks:
            return blocks, "ai"
    except Exception:
        pass
    return fallback, "deterministic"
