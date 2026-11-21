"""Active-area technical evidence scans, local retrieval probes, bulk scrubbing & diagnostics."""

import os
import platform
import shutil
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from core.contracts import KnowledgeChunk, SearchResult, WorkspaceConfig
from core.file_watcher import get_sync_status
from core.linked_vaults import is_linked_vault
from core.logging_config import log_file_path, recent_log_events
from core.runtime import is_frozen, is_loopback_url, ollama_base_url
from core.version import APP_VERSION
from features.ui import workspace
from features.ui.compliance_eval import benchmark
from features.ui.compliance_scan import scan_vault
from features.ui.hardware import physical_ram_gb

_STARTED_MONOTONIC = time.monotonic()
_ORIG_GET = httpx.get


def _probe_ollama_ps() -> list[str]:
    if os.environ.get("PYTEST_CURRENT_TEST") and httpx.get is _ORIG_GET:
        return []
    url = f"{ollama_base_url()}/api/ps"
    try:
        if httpx.get is _ORIG_GET:
            with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=0.8) as client:
                res = client.get(url)
        else:
            res = httpx.get(url, timeout=0.8)
        if res.status_code == 200 and isinstance((raw := res.json()), dict):
            return [str(m.get("name") or "") for m in (raw.get("models") or []) if isinstance(m, dict) and m.get("name")]
    except (httpx.HTTPError, ValueError, TypeError):
        pass
    return []


def build_router(config: Callable[[], WorkspaceConfig], index: Callable[[], list[KnowledgeChunk]], reindex: Callable[[Path], list[KnowledgeChunk]], inspect: Callable[[str, str], dict[str, object]], search: Callable[..., list[SearchResult]]) -> APIRouter:
    router = APIRouter()

    def report(request: Request, scrub: bool = False) -> JSONResponse:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.knowledge_dir:
                raise HTTPException(status_code=400, detail="Create or link a workspace before running a vault audit.")
            if scrub and is_linked_vault(active.knowledge_dir, workspace.REPO_ROOT):
                raise HTTPException(status_code=403, detail="Linked folders are read-safe — bulk scrubbing cannot modify external files on disk.")
            base = workspace.resolve_safe_knowledge_dir(active.knowledge_dir).resolve()
            vault = scan_vault(base, inspect, scrub)
            index_error = False
            try:
                chunks = reindex(base) if scrub else list(index())
                chunks = [c.model_copy(update={"doc_id": Path(c.file_path).resolve().relative_to(base).with_suffix("").as_posix()}) for c in chunks if Path(c.file_path).resolve().is_relative_to(base)]
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

    @router.get("/api/diagnostics")
    def diagnostics() -> JSONResponse:
        with workspace.STATE_LOCK:
            active = config()
            cur_chunks = list(index())
        root = workspace.REPO_ROOT
        writable = root.is_dir() and os.access(root, os.W_OK)
        try:
            disk_free_mb = round(shutil.disk_usage(root if root.exists() else root.parent).free / (1024 * 1024), 1)
        except OSError:
            disk_free_mb = -1.0
        payload: dict[str, object] = {
            "version": APP_VERSION,
            "mode": "local",
            "platform": f"{platform.system()} {platform.release()} ({platform.machine()})",
            "python_version": platform.python_version(),
            "frozen": is_frozen(),
            "uptime_seconds": round(time.monotonic() - _STARTED_MONOTONIC, 1),
            "data_dir_writable": writable,
            "disk_free_mb": disk_free_mb,
            "ram_gb": physical_ram_gb(),
            "active_areas": list(active.active_dirs),
            "strict_local_only": active.strict_local_only,
            "eco_mode": active.eco_mode,
            "chunk_count": len(cur_chunks),
            "embeddings_active": any(bool(c.embedding) for c in cur_chunks),
            "watcher": get_sync_status(),
            "ollama_loaded_models": _probe_ollama_ps(),
            "log_file_exists": log_file_path(root).is_file(),
            "recent_events": recent_log_events(25),
            "argv_mode": "desktop" if is_frozen() or "desktop_app" in sys.modules else "server",
        }
        return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    return router
