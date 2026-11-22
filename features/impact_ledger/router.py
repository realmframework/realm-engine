"""FastAPI router for Arbeitszeiterfassung, Wirksamkeitsdokumentation, and ROI Reports."""

from collections.abc import Callable, Mapping
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from core.ai_stream import (
    StreamMessagesFn,
    build_workspace_tutor_config,
    is_local_policy_satisfied,
    safe_download_filename,
)
from core.contracts import WorkspaceConfig
from core.impact_contracts import ImpactLedgerState
from core.json_store import require_area_header, store_lock
from features.impact_ledger import payloads, report, service, store

ProjectNamesFn = Callable[[str], dict[str, str]]


def _payload(state: ImpactLedgerState, area: str, extra: Mapping[str, object] | None = None) -> dict[str, object]:
    elapsed = service.elapsed_timer_seconds(state.active_timer) if state.active_timer else 0
    return {**state.model_dump(), "timer_elapsed_seconds": elapsed, "summary": store.compute_roi_summary(state), "area": area, **(extra or {})}


def log_focus_time(area: str, root: Path | None, label: str, minutes: float, project_id: str = "", task_id: str = "", notes: str = "") -> None:
    """Thread-safe callback invoked by app composition root when a Deep Focus session completes."""
    path = store.ledger_path(area, root)
    with store_lock(path):
        next_state, _ = service.add_time_entry(store.load_ledger(path), label, minutes, project_id=project_id, task_id=task_id, category="deep_focus", source="focus", notes=notes)
        store.save_ledger(next_state, path)


def log_workflow_impact(area: str, root: Path | None, what_done: str, effect: str, tag: str = "milestone") -> str:
    """Thread-safe callback invoked by workflow engine Log Impact node."""
    safe_tag = tag if tag in {"quality", "time_saved", "revenue", "wellbeing", "milestone"} else "milestone"
    path = store.ledger_path(area, root)
    with store_lock(path):
        next_state, entry = service.add_impact_entry(store.load_ledger(path), what_done, effect, outcome_tag=safe_tag)  # type: ignore[arg-type]
        store.save_ledger(next_state, path)
        return entry.id


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    stream_messages: StreamMessagesFn | None = None,
    project_names: ProjectNamesFn | None = None,
    root_provider: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _area_and_path(request: Request | None = None) -> tuple[WorkspaceConfig, Path]:
        cfg = get_config()
        if request is not None:
            require_area_header(request, cfg)
        return cfg, store.ledger_path(cfg.knowledge_dir, root_provider() if root_provider else None)

    def _mutate(request: Request, fn: Callable[[ImpactLedgerState], tuple[ImpactLedgerState, object]]) -> dict[str, object]:
        cfg, path = _area_and_path(request)
        with store_lock(path):
            try:
                next_state, item = fn(store.load_ledger(path))
                if item is None or item is False:
                    raise HTTPException(status_code=404, detail="Item not found")
                saved = store.save_ledger(next_state, path)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            extra: dict[str, object] = {"item": item.model_dump()} if isinstance(item, BaseModel) else {"ok": bool(item)}
            return _payload(saved, cfg.knowledge_dir, extra)

    @router.get("/api/impact")
    def get_impact() -> dict[str, object]:
        cfg, path = _area_and_path()
        with store_lock(path):
            return _payload(store.load_ledger(path), cfg.knowledge_dir)
    @router.patch("/api/impact/settings")
    def patch_settings(request: Request, body: payloads.ImpactSettingsBody) -> dict[str, object]:
        return _mutate(request, lambda s: (s.model_copy(update={"default_hourly_rate": body.default_hourly_rate, "currency": body.currency.upper()}), True))
    @router.post("/api/impact/timer/start")
    def api_start_timer(request: Request, body: payloads.TimerStartBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.start_timer(s, body.label, body.project_id, body.task_id, body.category, body.hourly_rate))
    @router.post("/api/impact/timer/toggle")
    def api_toggle_timer(request: Request) -> dict[str, object]:
        return _mutate(request, service.toggle_timer_pause)
    @router.post("/api/impact/timer/stop")
    def api_stop_timer(request: Request, body: payloads.TimerStopBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.stop_and_log_timer(s, body.notes))
    @router.delete("/api/impact/timer")
    def api_discard_timer(request: Request) -> dict[str, object]:
        return _mutate(request, lambda s: (s.model_copy(update={"active_timer": None}), True))
    @router.post("/api/impact/time")
    def api_add_time(request: Request, body: payloads.TimeEntryBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.add_time_entry(s, body.label, body.duration_minutes, body.date, body.project_id, body.task_id, body.category, body.hourly_rate, body.source, body.notes))
    @router.delete("/api/impact/time/{entry_id}")
    def api_del_time(request: Request, entry_id: str) -> dict[str, object]:
        return _mutate(request, lambda s: service.remove_time_entry(s, entry_id))
    @router.post("/api/impact/entries")
    def api_add_impact(request: Request, body: payloads.ImpactCreateBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.add_impact_entry(s, body.what_done, body.effect, body.date, body.project_id, body.evidence_notes, body.hours_invested, body.direct_cost, body.estimated_value, body.time_saved_hours, body.outcome_tag, body.task_ids))
    @router.patch("/api/impact/entries/{entry_id}")
    def api_edit_impact(request: Request, entry_id: str, body: payloads.ImpactPatchBody) -> dict[str, object]:
        return _mutate(request, lambda s: service.edit_impact_entry(s, entry_id, body.model_dump(exclude_unset=True)))
    @router.delete("/api/impact/entries/{entry_id}")
    def api_del_impact(request: Request, entry_id: str) -> dict[str, object]:
        return _mutate(request, lambda s: service.remove_impact_entry(s, entry_id))

    @router.post("/api/impact/draft")
    async def api_draft_impact(request: Request, body: payloads.ImpactDraftBody, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        cfg, _ = _area_and_path(request)
        can_ai = body.use_ai and stream_messages is not None and is_local_policy_satisfied(cfg, body.provider, body.model)
        tutor_cfg = build_workspace_tutor_config(cfg, body.provider, body.model, x_api_key, temperature=0.2) if can_ai else None
        draft, mode = await service.draft_impact_entry(body.notes, body.hours, stream_messages if can_ai else None, tutor_cfg, language=body.language)
        return {"draft": draft, "mode": mode}

    @router.get("/api/impact/timesheet.csv")
    def api_export_csv() -> Response:
        cfg, path = _area_and_path()
        with store_lock(path):
            csv_text = store.export_timesheet_csv(store.load_ledger(path))
        safe = safe_download_filename(cfg.knowledge_dir, "realm")
        return Response(content=csv_text.encode("utf-8"), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{safe}_timesheet.csv"', "Cache-Control": "no-store"})

    @router.post("/api/impact/report")
    def api_export_report(request: Request, body: payloads.ImpactReportBody) -> Response:
        cfg, path = _area_and_path(request)
        with store_lock(path):
            state = store.load_ledger(path)
        title = body.title.strip() or f"{cfg.app_title or 'REALM'} — Impact & ROI Report"
        pmap, safe = (project_names(cfg.knowledge_dir) if project_names else {}), safe_download_filename(cfg.knowledge_dir, "realm")
        if body.format == "pptx":
            data = report.render_impact_pptx(state, title, cfg.theme_accent, pmap)
            return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers={"Content-Disposition": f'attachment; filename="{safe}_impact_roi.pptx"', "Cache-Control": "no-store"})
        data = report.render_impact_pdf(state, title, pmap)
        return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{safe}_impact_roi.pdf"', "Cache-Control": "no-store"})

    return router
