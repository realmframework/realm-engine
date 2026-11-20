"""Active-area technical evidence scans, local retrieval probes and explicit bulk scrubbing."""

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from core.contracts import KnowledgeChunk, SearchResult, WorkspaceConfig
from features.ui import workspace
from features.ui.compliance_eval import benchmark
from features.ui.compliance_scan import scan_vault


def build_router(config: Callable[[], WorkspaceConfig], index: Callable[[], list[KnowledgeChunk]], reindex: Callable[[Path], list[KnowledgeChunk]], inspect: Callable[[str, str], dict[str, object]], search: Callable[..., list[SearchResult]]) -> APIRouter:
    router = APIRouter()

    def report(request: Request, scrub: bool = False) -> JSONResponse:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            base = workspace.resolve_safe_knowledge_dir(active.knowledge_dir)
            vault = scan_vault(base, inspect, scrub)
            index_error = False
            try:
                chunks = reindex(base) if scrub else list(index())
                chunks = [c.model_copy(update={"doc_id": Path(c.file_path).relative_to(base).with_suffix("").as_posix()}) for c in chunks if Path(c.file_path).is_relative_to(base)]
            except (OSError, UnicodeError, ValueError):
                chunks, index_error = [], True
                vault["clean_vault"] = False
            evaluation = benchmark(chunks, base, search)
            payload = {"area": active.knowledge_dir, "audited_at": datetime.now(UTC).isoformat(), "strict_local_only": active.strict_local_only, "audit_external_bytes_sent": 0, "index_error": index_error, **vault, "benchmark": evaluation, "limitations": "Pattern-based Markdown scan and retrieval diagnostics only; not a legal compliance certificate, clinical validation or complete PII detector. NAME detection uses filename hints. No generative-model evaluation or device-wide network measurement."}
            return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    @router.post("/api/compliance/audit")
    def audit(request: Request) -> JSONResponse:
        return report(request)

    @router.post("/api/compliance/scrub")
    def scrub(request: Request, payload: dict[str, bool]) -> JSONResponse:
        if payload.get("confirm") is not True:
            raise HTTPException(status_code=400, detail="Explicit scrub confirmation is required")
        return report(request, scrub=True)

    return router
