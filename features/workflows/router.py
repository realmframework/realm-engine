"""FastAPI router for Native Local Workflow & Agent Pipeline Studio (SSE + CRUD)."""

import json
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from threading import RLock

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse

from core.contracts import TutorConfig, WorkspaceConfig
from core.workflow_contracts import (
    WorkflowCreateBody,
    WorkflowPatchBody,
    WorkflowRun,
    WorkflowRunBody,
    WorkflowState,
)
from features.workflows import engine, store, templates

WORKFLOW_LOCK = RLock()


def _payload(state: WorkflowState, area: str, extra: dict[str, object] | None = None) -> dict[str, object]:
    return {**state.model_dump(), "templates": templates.template_catalog(store.utc_now()), "area": area, **(extra or {})}


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    callbacks_provider: Callable[[WorkspaceConfig], dict[str, object]],
    root_provider: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    def _area_path() -> tuple[WorkspaceConfig, Path]:
        cfg = get_config()
        return cfg, store.workflows_path(cfg.knowledge_dir, root_provider() if root_provider else None)

    def _save_run(area: str, run: WorkflowRun) -> None:
        with WORKFLOW_LOCK:
            path = store.workflows_path(area, root_provider() if root_provider else None)
            store.save_workflows(store.record_run(store.load_workflows(path), run), path)

    @router.get("/api/workflows")
    def api_list_workflows() -> dict[str, object]:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            return _payload(store.load_workflows(path), cfg.knowledge_dir)

    @router.post("/api/workflows")
    def api_create_workflow(body: WorkflowCreateBody) -> dict[str, object]:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            try:
                nxt, item = store.add_workflow(store.load_workflows(path), body.name, body.description, body.trigger_kind, body.schedule_minutes, body.nodes, body.edges, body.enabled)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            store.save_workflows(nxt, path)
            return _payload(nxt, cfg.knowledge_dir, {"item": item.model_dump()})

    @router.patch("/api/workflows/{wf_id}")
    def api_patch_workflow(wf_id: str, body: WorkflowPatchBody) -> dict[str, object]:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            try:
                nxt, item = store.update_workflow(store.load_workflows(path), wf_id, body.model_dump(exclude_unset=True))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if item is None:
                raise HTTPException(status_code=404, detail="Workflow not found")
            store.save_workflows(nxt, path)
            return _payload(nxt, cfg.knowledge_dir, {"item": item.model_dump()})

    @router.delete("/api/workflows/{wf_id}")
    def api_delete_workflow(wf_id: str) -> dict[str, object]:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            nxt, ok = store.delete_workflow(store.load_workflows(path), wf_id)
            if not ok:
                raise HTTPException(status_code=404, detail="Workflow not found")
            store.save_workflows(nxt, path)
            return _payload(nxt, cfg.knowledge_dir, {"ok": True})

    @router.post("/api/workflows/from-template/{template_id}")
    def api_install_template(template_id: str) -> dict[str, object]:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            nxt, item = store.install_template(store.load_workflows(path), template_id)
            if item is None:
                raise HTTPException(status_code=404, detail="Template not found")
            store.save_workflows(nxt, path)
            return _payload(nxt, cfg.knowledge_dir, {"item": item.model_dump()})

    @router.post("/api/workflows/{wf_id}/run/stream")
    async def api_run_stream(wf_id: str, body: WorkflowRunBody, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> StreamingResponse:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            wf = next((w for w in store.load_workflows(path).workflows if w.id == wf_id), None)
        if wf is None:
            raise HTTPException(status_code=404, detail="Workflow not found")
        if cfg.strict_local_only and body.provider != "ollama":
            raise HTTPException(status_code=403, detail="Local-Only Privacy Lock blocks cloud providers.")
        tcfg = TutorConfig(provider=body.provider, model=body.model, temperature=0.2)
        cbs, root = callbacks_provider(cfg), (root_provider() if root_provider else None)

        async def _gen() -> AsyncIterator[str]:
            async for ev in engine.run_workflow_stream(wf, body.input_text, body.trigger_source, cfg, tcfg, x_api_key, cbs, root):
                ev_name = str(ev.get("event") or "message")
                if ev_name == "run_done" and isinstance(ev.get("run"), dict):
                    _save_run(cfg.knowledge_dir, WorkflowRun.model_validate(ev["run"]))
                yield _sse(ev_name, ev)

        return StreamingResponse(_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})

    @router.post("/api/workflows/runs/{run_id}/cancel")
    def api_cancel_run(run_id: str) -> dict[str, object]:
        return {"run_id": run_id, "cancelled": engine.cancel_run(run_id)}

    @router.get("/api/workflows/runs")
    def api_list_runs() -> dict[str, object]:
        with WORKFLOW_LOCK:
            cfg, path = _area_path()
            return {"runs": [r.model_dump() for r in store.load_workflows(path).runs], "area": cfg.knowledge_dir}

    return router
