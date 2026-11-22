"""FastAPI router for Goal Seasons, Deep Focus Sessions, and AI Weekly Planner."""

from collections.abc import Callable, Mapping
from pathlib import Path
from threading import RLock

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from core.contracts import ProviderName, StrictModel, TutorConfig, WorkspaceConfig
from core.impact_contracts import (
    FocusState,
    GoalStatus,
    PlannedFocusBlock,
    SoundscapeMode,
)
from features.focus import service

FOCUS_LOCK = RLock()
_DATE_RE = r"^$|^\d{4}-\d{2}-\d{2}$"
OnSessionLoggedFn = Callable[[str, str, float, str, str, str], None]
GetOpenTasksFn = Callable[[str], list[dict[str, str]]]
ScheduleBlocksFn = Callable[[str, list[PlannedFocusBlock]], int]


class GoalCreateBody(StrictModel):
    title: str = Field(..., min_length=1, max_length=140)
    why: str = Field(default="", max_length=800)
    project_id: str = Field(default="", max_length=64)
    start_date: str = Field(default="", pattern=_DATE_RE)
    end_date: str = Field(default="", pattern=_DATE_RE)
    target_hours: float = Field(default=24.0, gt=0.0, le=2000.0)
    weekly_milestones: list[str] = Field(default_factory=list, max_length=24)
    status: GoalStatus = "active"


class GoalPatchBody(StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=140)
    why: str | None = Field(default=None, max_length=800)
    project_id: str | None = Field(default=None, max_length=64)
    start_date: str | None = Field(default=None, pattern=_DATE_RE)
    end_date: str | None = Field(default=None, pattern=_DATE_RE)
    target_hours: float | None = Field(default=None, gt=0.0, le=2000.0)
    weekly_milestones: list[str] | None = Field(default=None, max_length=24)
    status: GoalStatus | None = None


class FocusSessionBody(StrictModel):
    label: str = Field(..., min_length=1, max_length=180)
    planned_minutes: int = Field(default=45, ge=5, le=240)
    actual_minutes: float = Field(..., gt=0.0, le=480.0)
    quality_rating: int = Field(default=4, ge=1, le=5)
    soundscape: SoundscapeMode = "off"
    reflection: str = Field(default="", max_length=1000)
    goal_id: str = Field(default="", max_length=64)
    project_id: str = Field(default="", max_length=64)
    task_id: str = Field(default="", max_length=64)
    date: str = Field(default="", pattern=_DATE_RE)
    log_time: bool = True


class WeeklyPlanBody(StrictModel):
    use_ai: bool = True
    provider: ProviderName = "ollama"
    model: str = Field(default="qwen3:8b", min_length=1, max_length=120)
    language: str = Field(default="en", max_length=12)


class AcceptPlanBody(StrictModel):
    blocks: list[PlannedFocusBlock] = Field(..., min_length=1, max_length=14)


def _payload(state: FocusState, area: str, extra: Mapping[str, object] | None = None) -> dict[str, object]:
    return {**state.model_dump(), "analytics": service.focus_analytics(state), "area": area, **(extra or {})}


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    stream_messages: service.StreamMessagesFn | None = None,
    on_session_logged: OnSessionLoggedFn | None = None,
    get_open_tasks: GetOpenTasksFn | None = None,
    schedule_blocks: ScheduleBlocksFn | None = None,
    root_provider: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _area_and_path() -> tuple[WorkspaceConfig, Path]:
        cfg = get_config()
        return cfg, service.focus_path(cfg.knowledge_dir, root_provider() if root_provider else None)

    def _mutate(fn: Callable[[FocusState], tuple[FocusState, object]]) -> dict[str, object]:
        with FOCUS_LOCK:
            cfg, path = _area_and_path()
            next_state, item = fn(service.load_focus(path))
            if item is None or item is False:
                raise HTTPException(status_code=404, detail="Item not found")
            service.save_focus(next_state, path)
            extra: dict[str, object] = {"item": item.model_dump()} if isinstance(item, BaseModel) else {"ok": bool(item)}
            return _payload(next_state, cfg.knowledge_dir, extra)

    @router.get("/api/focus")
    def get_focus() -> dict[str, object]:
        with FOCUS_LOCK:
            cfg, path = _area_and_path()
            return _payload(service.load_focus(path), cfg.knowledge_dir)
    @router.post("/api/focus/goals")
    def api_add_goal(body: GoalCreateBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_goal(s, body.title, body.why, body.project_id, body.start_date, body.end_date, body.target_hours, body.weekly_milestones, body.status))
    @router.patch("/api/focus/goals/{goal_id}")
    def api_edit_goal(goal_id: str, body: GoalPatchBody) -> dict[str, object]:
        return _mutate(lambda s: service.edit_goal(s, goal_id, body.model_dump(exclude_unset=True)))
    @router.delete("/api/focus/goals/{goal_id}")
    def api_del_goal(goal_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_goal(s, goal_id))
    @router.post("/api/focus/sessions")
    def api_log_session(body: FocusSessionBody) -> dict[str, object]:
        res = _mutate(lambda s: service.add_session(s, body.label, body.planned_minutes, body.actual_minutes, body.quality_rating, body.soundscape, body.reflection, body.goal_id, body.project_id, body.task_id, body.date))
        if body.log_time and on_session_logged is not None:
            on_session_logged(str(res["area"]), body.label, body.actual_minutes, body.project_id, body.task_id, body.reflection)
        return res
    @router.delete("/api/focus/sessions/{session_id}")
    def api_del_session(session_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_session(s, session_id))

    @router.post("/api/focus/weekly-plan")
    async def api_weekly_plan(body: WeeklyPlanBody, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        with FOCUS_LOCK:
            cfg, path = _area_and_path()
            state = service.load_focus(path)
        open_tasks = get_open_tasks(cfg.knowledge_dir) if get_open_tasks else []
        can_ai = body.use_ai and stream_messages is not None and not (cfg.strict_local_only and body.provider != "ollama")
        tutor_cfg = TutorConfig(provider=body.provider, model=body.model, api_key=x_api_key or None, temperature=0.2) if can_ai else None
        blocks, mode = await service.generate_weekly_plan(state, open_tasks, stream_messages if can_ai else None, tutor_cfg, language=body.language)
        return {"blocks": [b.model_dump() for b in blocks], "mode": mode}

    @router.post("/api/focus/weekly-plan/accept")
    def api_accept_plan(body: AcceptPlanBody) -> dict[str, object]:
        if schedule_blocks is None:
            raise HTTPException(status_code=501, detail="Calendar integration unavailable")
        cfg = get_config()
        added = schedule_blocks(cfg.knowledge_dir, body.blocks)
        return {"ok": True, "scheduled_count": added}

    return router
