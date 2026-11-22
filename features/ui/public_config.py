"""Environment configuration and read-only snapshot loading for REALM_MODE=public."""

import os
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.contracts import (
    KnowledgeArea,
    KnowledgeChunk,
    ProviderName,
    ReasoningEffort,
    SearchResult,
    TutorResponse,
    WorkspaceConfig,
)
from core.db import load_chunks
from core.http_guard import install_safe_error_handlers
from core.runtime import data_root
from core.scope import resolve_chunk_url
from core.version import APP_VERSION
from features.ui import areas, public_rate_limit, public_routes, selection
from features.ui.upload_guard import public_body_guard

VALID_PROVIDERS: set[str] = {"ollama", "openai", "kimi", "deepseek", "gemini", "anthropic", "xai", "mistral"}
VALID_EFFORTS: set[str] = {"low", "medium", "high", "max"}


def load_public_settings() -> dict[str, object]:
    """Read immutable server-side settings for the read-only public API."""
    raw_provider = os.environ.get("REALM_PUBLIC_PROVIDER", "kimi").strip().lower()
    provider: ProviderName = raw_provider if raw_provider in VALID_PROVIDERS else "kimi"  # type: ignore[assignment]
    model = os.environ.get("REALM_PUBLIC_MODEL", "").strip()
    raw_effort = os.environ.get("REALM_PUBLIC_REASONING_EFFORT", "low" if provider == "kimi" else "").strip().lower()
    effort: ReasoningEffort | None = raw_effort if raw_effort in VALID_EFFORTS else None  # type: ignore[assignment]
    raw_areas = [item.strip() for item in os.environ.get("REALM_PUBLIC_AREAS", "").split(",") if item.strip()]
    origins = [item.strip() for item in os.environ.get("REALM_PUBLIC_ORIGINS", "").split(",") if item.strip()]
    return {
        "areas": raw_areas,
        "provider": provider,
        "model": model,
        "reasoning_effort": effort,
        "embed_provider": os.environ.get("REALM_PUBLIC_EMBED_PROVIDER", "").strip().lower(),
        "url_template": os.environ.get("REALM_PUBLIC_URL_TEMPLATE", "/knowledge/{area}/{doc_id}").strip(),
        "origins": origins,
        "ip_rpm": max(1, int(os.environ.get("REALM_PUBLIC_IP_RPM", "5"))),
        "ip_daily": max(1, int(os.environ.get("REALM_PUBLIC_IP_DAILY", "25"))),
        "global_daily": max(0, int(os.environ.get("REALM_PUBLIC_DAILY_LIMIT", "300"))),
        "global_usd": max(0.0, float(os.environ.get("REALM_PUBLIC_DAILY_USD", "1.0"))),
        "trust_proxy": os.environ.get("REALM_PUBLIC_TRUST_PROXY", "0").strip().lower() in {"1", "true", "yes"},
        "trusted_hops": max(1, int(os.environ.get("REALM_PUBLIC_TRUSTED_HOPS", "1"))),
    }


def _load_readonly_area(directory: Path, ingest: Callable[[Path], list[KnowledgeChunk]]) -> list[KnowledgeChunk]:
    cache = directory / "index.json"
    if cache.is_file() and not cache.is_symlink():
        try:
            if cached := load_chunks(cache):
                return cached
        except (ValueError, OSError, TypeError, AttributeError):
            pass
    return ingest(directory)

def _load_exclusions(root: Path) -> dict[str, list[str]]:
    ws_path = root / "workspace.json"
    if ws_path.is_file() and not ws_path.is_symlink():
        try:
            return WorkspaceConfig.model_validate_json(ws_path.read_text(encoding="utf-8")).excluded_subfolders
        except (ValueError, OSError):
            pass
    return {}


def load_public_snapshot(
    root: Path,
    configured_areas: list[str],
    url_template: str,
    ingest: Callable[[Path], list[KnowledgeChunk]],
) -> tuple[list[KnowledgeArea], list[KnowledgeChunk]]:
    """Pre-load explicitly configured vaults read-only into memory (fail-closed if none configured)."""
    if not configured_areas:
        return [], []
    root.mkdir(parents=True, exist_ok=True)
    discovered = areas.list_areas(root, configured_areas[0])
    exclusions = _load_exclusions(root)
    color_by_name = {a.name: a.color for a in discovered}
    published_areas: list[KnowledgeArea] = []
    all_chunks: list[KnowledgeChunk] = []

    for idx, name in enumerate(dict.fromkeys(configured_areas)):
        try:
            directory = areas.area_path(name, root, create=False)
        except ValueError:
            continue
        raw_chunks = _load_readonly_area(directory, ingest)
        excl = exclusions.get(name, [])
        enriched: list[KnowledgeChunk] = []
        for chunk in raw_chunks:
            if excl and selection.is_excluded(chunk.subfolder, excl):
                continue
            local_doc = chunk.doc_id or Path(chunk.file_path).stem
            tagged = chunk.model_copy(update={"area": name, "id": f"{name}::{chunk.id}", "doc_id": local_doc, "file_path": ""})
            url = public_routes.safe_public_url(resolve_chunk_url(tagged, url_template))
            enriched.append(tagged.model_copy(update={"url": url}))
        all_chunks.extend(enriched)
        doc_count = len({c.doc_id for c in enriched})
        color = color_by_name.get(name, areas.AREA_COLORS[idx % len(areas.AREA_COLORS)])
        published_areas.append(KnowledgeArea(name=name, doc_count=doc_count, color=color, can_delete=False))
    return published_areas, all_chunks


def build_public_fastapi(
    ingest: Callable[[Path], list[KnowledgeChunk]],
    route_intent: Callable[..., dict[str, object]],
    search_fn: Callable[..., list[SearchResult]],
    embed_fn: Callable[..., list[float]],
    tutor_fn: Callable[..., TutorResponse],
    estimate_fn: Callable[..., tuple[int, float]],
    data_dir: Path | None = None,
    quota_check: public_rate_limit.QuotaChecker | None = None,
) -> FastAPI:
    """Create a stateless, read-only public API FastAPI app without local admin/write routes."""
    settings = load_public_settings()
    root = (data_dir or data_root()).expanduser().resolve()
    raw_areas = settings.get("areas")
    configured = [str(a) for a in raw_areas] if isinstance(raw_areas, list) else []
    published, snapshot = load_public_snapshot(root, configured, str(settings["url_template"]), ingest)
    public_app = FastAPI(title="REALM Engine — Public API", version=APP_VERSION)
    install_safe_error_handlers(public_app)
    public_app.add_middleware(public_body_guard)
    origins = settings.get("origins")
    if isinstance(origins, list) and origins:
        public_app.add_middleware(CORSMiddleware, allow_origins=[str(o) for o in origins], allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])
    public_app.add_api_route("/healthz", lambda: {"status": "ok", "mode": "public", "version": APP_VERSION}, methods=["GET"])
    limiter = quota_check or public_rate_limit.build_public_limiter(settings)
    public_app.include_router(public_routes.build_router(published, snapshot, settings, route_intent, search_fn, embed_fn, tutor_fn, estimate_fn, limiter))
    return public_app
