"""FastAPI router for Arbeitszeiterfassung, Wirksamkeitsdokumentation, and ROI Reports."""

from collections.abc import Callable, Mapping
from pathlib import Path
from threading import RLock

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from core.contracts import TutorConfig, WorkspaceConfig
from core.impact_contracts import ImpactLedgerState
from features.impact_ledger import payloads, report, service, store

IMPACT_LOCK = RLock()
ProjectNamesFn = Callable[[str], dict[str, str]]


def _payload(state: ImpactLedgerState, area: str, extra: Mapping[str, object] | None = None) -> dict[str, object]:
    elapsed = service.elapsed_timer_seconds(state.active_timer) if state.active_timer else 0
    return {**state.model_dump(), "timer_elapsed_seconds": elapsed, "summary": store.compute_roi_summary(state), "area": area, **(extra or {})}


def log_focus_time(area: str, root: Path | None, label: str, minutes: float, project_id: str = "", task_id: str = "", notes: str = "") -> None:
    """Thread-safe callback invoked by app composition root when a Deep Focus session completes."""
    with IMPACT_LOCK:
        path = store.ledger_path(area, root)
        state = store.load_ledger(path)
        next_state, _ = service.add_time_entry(state, label, minutes, project_id=project_id, task_id=task_id, category="deep_focus", source="focus", notes=notes)
        store.save_ledger(next_state, path)


def log_workflow_impact(area: str, root: Path | None, what_done: str, effect: str, tag: str = "milestone") -> str:
    """Thread-safe callback invoked by workflow engine Log Impact node."""
    valid_tags = {"quality", "time_saved", "revenue", "wellbeing", "milestone"}
    safe_tag = tag if tag in valid_tags else "milestone"
    with IMPACT_LOCK:
        path = store.ledger_path(area, root)
        state = store.load_ledger(path)
        next_state, entry = service.add_impact_entry(state, what_done, effect, outcome_tag=safe_tag)  # type: ignore[arg-type]
        store.save_ledger(next_state, path)
        return entry.id


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    stream_messages: service.StreamMessagesFn | None = None,
    project_names: ProjectNamesFn | None = None,
    root_provider: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _area_and_path() -> tuple[WorkspaceConfig, Path]:
        cfg = get_config()
        return cfg, store.ledger_path(cfg.knowledge_dir, root_provider() if root_provider else None)

    def _mutate(fn: Callable[[ImpactLedgerState], tuple[ImpactLedgerState, object]]) -> dict[str, object]:
        with IMPACT_LOCK:
            cfg, path = _area_and_path()
            next_state, item = fn(store.load_ledger(path))
            if item is None or item is False:
                raise HTTPException(status_code=404, detail="Item not found")
            store.save_ledger(next_state, path)
            extra: dict[str, object] = {"item": item.model_dump()} if isinstance(item, BaseModel) else {"ok": bool(item)}
            return _payload(next_state, cfg.knowledge_dir, extra)

    @router.get("/api/impact")
    def get_impact() -> dict[str, object]:
        with IMPACT_LOCK:
            cfg, path = _area_and_path()
            return _payload(store.load_ledger(path), cfg.knowledge_dir)

    @router.patch("/api/impact/settings")
    def patch_settings(body: payloads.ImpactSettingsBody) -> dict[str, object]:
        return _mutate(lambda s: (s.model_copy(update={"default_hourly_rate": body.default_hourly_rate, "currency": body.currency.upper()}), True))

    @router.post("/api/impact/timer/start")
    def api_start_timer(body: payloads.TimerStartBody) -> dict[str, object]:
        return _mutate(lambda s: service.start_timer(s, body.label, body.project_id, body.task_id, body.category, body.hourly_rate))

    @router.post("/api/impact/timer/toggle")
    def api_toggle_timer() -> dict[str, object]:
        return _mutate(service.toggle_timer_pause)

    @router.post("/api/impact/timer/stop")
    def api_stop_timer(body: payloads.TimerStopBody) -> dict[str, object]:
        return _mutate(lambda s: service.stop_and_log_timer(s, body.notes))

    @router.delete("/api/impact/timer")
    def api_discard_timer() -> dict[str, object]:
        return _mutate(lambda s: (s.model_copy(update={"active_timer": None}), True))

    @router.post("/api/impact/time")
    def api_add_time(body: payloads.TimeEntryBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_time_entry(s, body.label, body.duration_minutes, body.date, body.project_id, body.task_id, body.category, body.hourly_rate, body.source, body.notes))

    @router.delete("/api/impact/time/{entry_id}")
    def api_del_time(entry_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_time_entry(s, entry_id))

    @router.post("/api/impact/entries")
    def api_add_impact(body: payloads.ImpactCreateBody) -> dict[str, object]:
        return _mutate(lambda s: service.add_impact_entry(s, body.what_done, body.effect, body.date, body.project_id, body.evidence_notes, body.hours_invested, body.direct_cost, body.estimated_value, body.time_saved_hours, body.outcome_tag, body.task_ids))

    @router.patch("/api/impact/entries/{entry_id}")
    def api_edit_impact(entry_id: str, body: payloads.ImpactPatchBody) -> dict[str, object]:
        return _mutate(lambda s: service.edit_impact_entry(s, entry_id, body.model_dump(exclude_unset=True)))

    @router.delete("/api/impact/entries/{entry_id}")
    def api_del_impact(entry_id: str) -> dict[str, object]:
        return _mutate(lambda s: service.remove_impact_entry(s, entry_id))

    @router.post("/api/impact/draft")
    async def api_draft_impact(body: payloads.ImpactDraftBody, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        cfg = get_config()
        can_ai = body.use_ai and stream_messages is not None and not (cfg.strict_local_only and body.provider != "ollama")
        tutor_cfg = TutorConfig(provider=body.provider, model=body.model, api_key=x_api_key or None, temperature=0.2) if can_ai else None
        draft, mode = await service.draft_impact_entry(body.notes, body.hours, stream_messages if can_ai else None, tutor_cfg, language=body.language)
        return {"draft": draft, "mode": mode}

    @router.get("/api/impact/timesheet.csv")
    def api_export_csv() -> Response:
        with IMPACT_LOCK:
            cfg, path = _area_and_path()
            csv_text = store.export_timesheet_csv(store.load_ledger(path))
        safe = (cfg.knowledge_dir or "realm").replace('"', "")
        return Response(content=csv_text.encode("utf-8"), media_type="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename="{safe}_timesheet.csv"', "Cache-Control": "no-store"})

    @router.post("/api/impact/report")
    def api_export_report(body: payloads.ImpactReportBody) -> Response:
        with IMPACT_LOCK:
            cfg, path = _area_and_path()
            state = store.load_ledger(path)
        title = body.title.strip() or f"{cfg.app_title or 'REALM'} — Impact & ROI Report"
        pmap = project_names(cfg.knowledge_dir) if project_names else {}
        safe = (cfg.knowledge_dir or "realm").replace('"', "")
        if body.format == "pptx":
            data = report.render_impact_pptx(state, title, cfg.theme_accent, pmap)
            return Response(content=data, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", headers={"Content-Disposition": f'attachment; filename="{safe}_impact_roi.pptx"', "Cache-Control": "no-store"})
        data = report.render_impact_pdf(state, title, pmap)
        return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{safe}_impact_roi.pdf"', "Cache-Control": "no-store"})

    return router
