"""Goal Seasons trajectory analytics, Deep Focus session store, and AI/offline Weekly Coach."""

import json
import re
from datetime import date, timedelta
from pathlib import Path

from core.ai_stream import StreamMessagesFn, collect_stream_text
from core.contracts import TutorConfig
from core.impact_contracts import (
    FocusSession,
    FocusState,
    GoalSeason,
    GoalStatus,
    PlannedFocusBlock,
    SoundscapeMode,
)
from core.json_store import (
    area_store_path,
    load_model_json,
    new_id,
    save_model_json,
    store_lock,
    today_iso,
    utc_now,
    validate_iso_date,
)

__all__ = [
    "StreamMessagesFn", "add_goal", "add_session", "edit_goal", "focus_analytics",
    "focus_path", "generate_weekly_plan", "goal_trajectory", "load_focus",
    "new_id", "remove_goal", "remove_session", "save_focus", "store_lock",
    "today_iso", "utc_now",
]


def focus_path(area: str, root: Path | None = None) -> Path:
    return area_store_path(area, "focus_engine.json", root)


def load_focus(path: Path) -> FocusState:
    return load_model_json(path, FocusState, FocusState)


def save_focus(state: FocusState, path: Path) -> FocusState:
    return save_model_json(state, path, FocusState)


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
    s_date = validate_iso_date(start_date, allow_empty=True, field_name="start_date") or today_iso()
    e_date = validate_iso_date(end_date, allow_empty=True, field_name="end_date") or (date.fromisoformat(s_date) + timedelta(days=84)).isoformat()
    goal = GoalSeason(id=new_id("gol"), title=title.strip(), why=why.strip(), project_id=project_id.strip(), start_date=s_date, end_date=e_date, target_hours=max(1.0, float(target_hours)), weekly_milestones=[m.strip() for m in (weekly_milestones or []) if m.strip()][:24], status=status, created_at=utc_now())
    return state.model_copy(update={"goals": [*state.goals, goal]}), goal


def edit_goal(state: FocusState, goal_id: str, updates: dict[str, object]) -> tuple[FocusState, GoalSeason | None]:
    clean = {k: (v.strip() if isinstance(v, str) else v) for k, v in updates.items() if v is not None}
    if "start_date" in clean:
        clean["start_date"] = validate_iso_date(str(clean["start_date"]), allow_empty=False, field_name="start_date")
    if "end_date" in clean:
        clean["end_date"] = validate_iso_date(str(clean["end_date"]), allow_empty=False, field_name="end_date")
    items, found = [], None
    for g in state.goals:
        if g.id == goal_id:
            found = GoalSeason.model_validate({**g.model_dump(), **clean})
            items.append(found)
        else:
            items.append(g)
    return (state.model_copy(update={"goals": items}), found) if found else (state, None)


def remove_goal(state: FocusState, goal_id: str) -> tuple[FocusState, bool]:
    kept = [g for g in state.goals if g.id != goal_id]
    return (state.model_copy(update={"goals": kept}), True) if len(kept) != len(state.goals) else (state, False)


def add_session(state: FocusState, label: str, planned_minutes: int, actual_minutes: float, quality_rating: int = 4, soundscape: SoundscapeMode = "off", reflection: str = "", goal_id: str = "", project_id: str = "", task_id: str = "", date_str: str = "") -> tuple[FocusState, FocusSession]:
    safe_dt = validate_iso_date(date_str, allow_empty=True, field_name="date") or today_iso()
    sess = FocusSession(id=new_id("foc"), date=safe_dt, goal_id=goal_id.strip(), project_id=project_id.strip(), task_id=task_id.strip(), label=label.strip(), planned_minutes=planned_minutes, actual_minutes=round(float(actual_minutes), 1), quality_rating=quality_rating, soundscape=soundscape, reflection=reflection.strip(), completed_at=utc_now())
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
    try:
        raw = await collect_stream_text(stream_messages, [{"role": "system", "content": sys_p}, {"role": "user", "content": ctx}], tutor_config)
    except Exception:
        return fallback, "deterministic"
    m = re.search(r"<plan_json>\s*(\[.*?\])\s*</plan_json>", raw, re.DOTALL)
    try:
        parsed = json.loads(m.group(1) if m else raw[raw.find("[") : raw.rfind("]") + 1])
        blocks = [PlannedFocusBlock.model_validate(b) for b in parsed[:7] if isinstance(b, dict)]
        if blocks:
            return blocks, "ai"
    except Exception:
        pass
    return fallback, "deterministic"
