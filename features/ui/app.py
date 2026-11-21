"""FastAPI composition root supporting local desktop/Docker and read-only public API modes."""

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from core import contracts, secrets
from core.db import load_chunks, save_chunks
from core.linked_vaults import cache_index_for_dir
from core.runtime import app_mode, bundle_root
from features.ingestion import converters
from features.ingestion.anonymizer import anonymize_slug, inspect_anonymization
from features.ingestion.embedder import (
    embed_text,
    hydrate_embeddings,
    reset_ollama_status,
)
from features.ingestion.service import ingest_directory
from features.search.router import route_query_intent
from features.search.service import hybrid_search
from features.tutor_agent import budget
from features.tutor_agent.models_discovery import discover_models
from features.tutor_agent.providers import list_provider_models
from features.tutor_agent.service import ask_tutor as run_tutor
from features.tutor_agent.streaming import stream_messages_events, stream_tutor_events
from features.ui import (
    appearance_routes,
    area_routes,
    audio_routes,
    backup_routes,
    budget_routes,
    chat_routes,
    compliance_routes,
    document_routes,
    model_routes,
    public_config,
    public_rate_limit,
    query_routes,
    selection,
    workspace,
    workspace_templates,
)
from features.ui.cloud_access import build_embedder, build_guard
from features.ui.hardware import hardware_advice
from features.ui.privacy import require_local
from features.ui.startup import area_lifespan
from features.ui.template import HTML_PAGE
from features.ui.upload_guard import upload_body_guard

STATIC_DIR = bundle_root() / "features" / "ui" / "static"
secrets.load_dotenv_files()
AUTO_EMBED = os.environ.get("REALM_AUTO_EMBED", "1").strip().lower() not in {"0", "false", "no"}
WORKSPACE_CONFIG = workspace.load_workspace_config()
INDEX: list[contracts.KnowledgeChunk] = []


def _load_area(target: Path) -> list[contracts.KnowledgeChunk]:
    cache = cache_index_for_dir(target, workspace.REPO_ROOT)
    if cache.is_symlink():
        raise HTTPException(status_code=400, detail="Area index cannot be a symbolic link")
    cached = load_chunks(cache) if cache.is_file() else []
    chunks = hydrate_embeddings(ingest_directory(target), cached, embed_missing=AUTO_EMBED)
    save_chunks(chunks, cache)
    return chunks


def _reindex(target_dir: Path) -> list[contracts.KnowledgeChunk]:
    global INDEX
    INDEX = selection.merge(WORKSPACE_CONFIG, workspace.REPO_ROOT, _load_area) if len(WORKSPACE_CONFIG.active_dirs) > 1 else selection.filter_chunks(_load_area(target_dir), WORKSPACE_CONFIG.knowledge_dir, WORKSPACE_CONFIG)
    return INDEX


def get_index() -> list[contracts.KnowledgeChunk]:
    with workspace.STATE_LOCK:
        if len(WORKSPACE_CONFIG.active_dirs) > 1:
            try:
                selection.paths(WORKSPACE_CONFIG, workspace.REPO_ROOT)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        return INDEX or _reindex(workspace.resolve_safe_knowledge_dir(WORKSPACE_CONFIG.knowledge_dir, create=True))


def activate_workspace(config: contracts.WorkspaceConfig) -> dict[str, object]:
    global WORKSPACE_CONFIG, INDEX
    with workspace.STATE_LOCK:
        try:
            chunks = selection.merge(config, workspace.REPO_ROOT, _load_area) if len(config.active_dirs) > 1 else selection.filter_chunks(_load_area(workspace.resolve_safe_knowledge_dir(config.knowledge_dir, create=True)), config.knowledge_dir, config)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        workspace.save_workspace_config(config)
        INDEX, WORKSPACE_CONFIG = chunks, config
        return workspace.build_workspace_payload(config, chunks)


def _set_workspace_config(config: contracts.WorkspaceConfig) -> None:
    global WORKSPACE_CONFIG
    WORKSPACE_CONFIG = config


def build_public_app(data_dir: Path | None = None, quota_check: public_rate_limit.QuotaChecker | None = None) -> FastAPI:
    """Create a stateless, read-only public API FastAPI app without local admin/write routes."""
    return public_config.build_public_fastapi(
        ingest_directory, route_query_intent, hybrid_search,
        lambda *a, **kw: embed_text(*a, **kw), lambda *a, **kw: run_tutor(*a, **kw),
        budget.estimate_usage, data_dir=data_dir, quota_check=quota_check,
    )


def _build_local_app() -> FastAPI:
    local = FastAPI(title="REALM Engine", lifespan=area_lifespan(converters.repair_directory_topics))
    local.add_middleware(upload_body_guard)
    local.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    cloud_guard = build_guard(lambda: WORKSPACE_CONFIG, budget.check_and_record_budget, budget.estimate_usage)
    audio_routes.privacy_config, audio_routes.cloud_admission = (lambda: WORKSPACE_CONFIG), cloud_guard
    for router in (
        appearance_routes.build_router(lambda: WORKSPACE_CONFIG, _set_workspace_config),
        backup_routes.build_router(lambda: WORKSPACE_CONFIG, activate_workspace),
        workspace_templates.build_router(lambda: WORKSPACE_CONFIG, activate_workspace),
        model_routes.build_router(lambda: WORKSPACE_CONFIG, reset_ollama_status), audio_routes.router,
        chat_routes.build_router(lambda: WORKSPACE_CONFIG, converters.convert_bytes_to_markdown, stream_messages_events),
        document_routes.build_router(lambda: WORKSPACE_CONFIG, _reindex, converters.convert_bytes_to_markdown, inspect_anonymization, anonymize_slug),
        area_routes.build_router(lambda: WORKSPACE_CONFIG, activate_workspace, get_index, ingest_directory),
        query_routes.build_router(lambda: WORKSPACE_CONFIG, get_index, route_query_intent, hybrid_search, build_embedder(lambda *a, **kw: embed_text(*a, **kw), cloud_guard), lambda *args, **kwargs: run_tutor(*args, **kwargs), stream_tutor_events),
        compliance_routes.build_router(lambda: WORKSPACE_CONFIG, get_index, _reindex, inspect_anonymization, hybrid_search),
        budget_routes.build_router(lambda: WORKSPACE_CONFIG, budget.budget_snapshot, budget.reset_budget),
    ):
        local.include_router(router)
    local.add_api_route("/favicon.ico", lambda: FileResponse(STATIC_DIR / "favicon.ico"), methods=["GET"], include_in_schema=False)
    local.add_api_route("/healthz", lambda: {"status": "ok", "mode": "local"}, methods=["GET"])
    local.add_api_route("/", lambda: HTMLResponse(content=HTML_PAGE), methods=["GET"], response_class=HTMLResponse)

    @local.get("/api/system-status")
    def get_system_status() -> dict[str, object]:
        st, hw = workspace.probe_system_status(get_index()), hardware_advice()
        raw = st.get("ollama_models")
        return {**st, **hw, "recommended_local_model": model_routes.recommended_model(int(str(hw["ram_gb"]))), **discover_models([str(m) for m in raw] if isinstance(raw, list) else [])}

    @local.get("/api/models")
    def api_models(provider: contracts.ProviderName = "ollama", x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        require_local(WORKSPACE_CONFIG, provider)
        models = list_provider_models(provider, x_api_key)
        return {"provider": provider, "models": models, "chat_models": models}

    return local


app = build_public_app() if app_mode() == "public" else _build_local_app()
