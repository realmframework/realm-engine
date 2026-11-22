"""FastAPI router for Goal Seasons, Deep Focus Sessions, and AI Weekly Planner."""

from collections.abc import Callable, Mapping
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from core import ai_stream, json_store
from core.contracts import WorkspaceConfig
from core.impact_contracts import FocusState, PlannedFocusBlock
from features.focus import payloads, service

OnSessionLoggedFn = Callable[[str, str, float, str, str, str], None]
GetOpenTasksFn = Callable[[str], list[dict[str, str]]]
ScheduleBlocksFn = Callable[[str, list[PlannedFocusBlock]], int]


def _payload(state: FocusState, area: str, extra: Mapping[str, object] | None = None) -> dict[str, object]:
    return {**state.model_dump(), "analytics": service.focus_analytics(state), "area": area, **(extra or {})}


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    stream_messages: ai_stream.StreamMessagesFn | None = None,
    on_session_logged: OnSessionLoggedFn | None = None,
    get_open_tasks: GetOpenTasksFn | None = None,
    schedule_blocks: ScheduleBlocksFn | None = None,
    root_provider: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _area_and_path(request: Request | None = None) -> tuple[WorkspaceConfig, Path]:
        cfg = get_config()
        if request is not None:
            json_store.require_area_header(request, cfg)
        return cfg, service.focus_path(cfg.knowledge_dir, root_provider() if root_provider else None)

    def _mutate(request: Request, fn: Callable[[FocusState], tuple[FocusState, object]]) -> dict[str, object]:
        cfg, path = _area_and_path(request)
        with json_store.store_lock(path):
            try:
                next_state, item = fn(service.load_focus(path))
                if item is None or item is False:
                    raise HTTPException(status_code=404, detail="Item not found")
                saved = service.save_focus(next_state, path)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            extra: dict[str, object] = {"item": item.model_dump()} if isinstance(item, BaseModel) else {"ok": bool(item)}
            return _payload(saved, cfg.knowledge_dir, extra)

    @router.get("/api/focus")
    def get_focus() -> dict[str, object]:
        cfg, path = _area_and_path()
        with json_store.store_lock(path):
            return _payload(service.load_focus(path), cfg.knowledge_dir)

    @router.post("/api/focus/goals")
    def api_add_goal(request: Request, body: payloads.GoalCreateBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.add_goal(s, body.title, body.why, body.project_id, body.start_date, body.end_date, body.target_hours, body.weekly_milestones, body.status))

    @router.patch("/api/focus/goals/{goal_id}")
    def api_edit_goal(request: Request, goal_id: str, body: payloads.GoalPatchBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.edit_goal(s, goal_id, body.model_dump(exclude_unset=True)))

    @router.delete("/api/focus/goals/{goal_id}")
    def api_del_goal(request: Request, goal_id: str) -> dict[str, object]:
        return _mutate(request, lambda s: service.remove_goal(s, goal_id))

    @router.post("/api/focus/sessions")
    def api_log_session(request: Request, body: payloads.FocusSessionBody) -> dict[str, object]:
        res = _mutate(request, lambda s: service.add_session(s, body.label, body.planned_minutes, body.actual_minutes, body.quality_rating, body.soundscape, body.reflection, body.goal_id, body.project_id, body.task_id, body.date))
        if body.log_time and on_session_logged is not None:
            on_session_logged(str(res["area"]), body.label, body.actual_minutes, body.project_id, body.task_id, body.reflection)
        return res

    @router.delete("/api/focus/sessions/{session_id}")
    def api_del_session(request: Request, session_id: str) -> dict[str, object]:
        return _mutate(request, lambda s: service.remove_session(s, session_id))

    @router.post("/api/focus/weekly-plan")
    async def api_weekly_plan(request: Request, body: payloads.WeeklyPlanBody, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        cfg, path = _area_and_path(request)
        with json_store.store_lock(path):
            state = service.load_focus(path)
        open_tasks = get_open_tasks(cfg.knowledge_dir) if get_open_tasks else []
        can_ai = body.use_ai and stream_messages is not None and ai_stream.is_local_policy_satisfied(cfg, body.provider, body.model)
        tutor_cfg = ai_stream.build_workspace_tutor_config(cfg, body.provider, body.model, x_api_key, temperature=0.2) if can_ai else None
        blocks, mode = await service.generate_weekly_plan(state, open_tasks, stream_messages if can_ai else None, tutor_cfg, language=body.language)
        return {"blocks": [b.model_dump() for b in blocks], "mode": mode}

    @router.post("/api/focus/weekly-plan/accept")
    def api_accept_plan(request: Request, body: payloads.AcceptPlanBody) -> dict[str, object]:
        if schedule_blocks is None:
            raise HTTPException(status_code=501, detail="Calendar integration unavailable")
        cfg, _ = _area_and_path(request)
        return {"ok": True, "scheduled_count": schedule_blocks(cfg.knowledge_dir, body.blocks)}

    return router
