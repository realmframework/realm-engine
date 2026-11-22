"""FastAPI routes for Built-in Private AI status, SSE setup, config, sleep & uninstall."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from core.local_ai_contracts import LocalAiConfigUpdate, LocalAiSetupRequest
from core.local_ai_sidecar import shutdown_sidecar
from features.local_ai import service


def _sse_stream(events: Iterator[dict[str, object]]) -> Iterator[str]:
    for item in events:
        ev = str(item.get("event") or "message")
        data = json.dumps(item.get("data") or {})
        yield f"event: {ev}\ndata: {data}\n\n"


def build_router(get_root: Callable[[], Path]) -> APIRouter:
    router = APIRouter(prefix="/api/local-ai", tags=["local-ai"])

    @router.get("/status")
    def local_ai_status() -> dict[str, object]:
        return service.get_status(get_root()).model_dump(mode="json")

    @router.post("/setup/stream")
    def local_ai_setup_stream(payload: LocalAiSetupRequest) -> StreamingResponse:
        events = service.stream_setup_events(payload, get_root())
        return StreamingResponse(_sse_stream(events), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})

    @router.post("/cancel-setup")
    def local_ai_cancel_setup() -> dict[str, bool]:
        return {"cancelled": service.cancel_setup()}

    @router.post("/config")
    def local_ai_update_config(payload: LocalAiConfigUpdate) -> dict[str, object]:
        return service.update_config(payload, get_root()).model_dump(mode="json")

    @router.post("/unload")
    def local_ai_unload() -> dict[str, object]:
        stopped = shutdown_sidecar()
        return {"stopped": stopped, "status": service.get_status(get_root()).model_dump(mode="json")}

    @router.delete("/runtime")
    def local_ai_uninstall() -> dict[str, object]:
        return service.uninstall_runtime(get_root())

    return router
