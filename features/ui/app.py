"""FastAPI composition root supporting local desktop/Docker and read-only public API modes."""

import os
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from core import contracts, secrets
from core.db import load_chunks_meta, save_chunks
from core.http_guard import install_safe_error_handlers
from core.linked_vaults import cache_index_for_dir
from core.runtime import app_mode, bundle_root
from core.version import APP_VERSION
from features.focus import router as focus_router
from features.impact_ledger import router as impact_router
from features.ingestion import converters, embedder
from features.ingestion.anonymizer import anonymize_slug, inspect_anonymization
from features.ingestion.embedder import embed_text
from features.ingestion.service import ingest_directory
from features.local_ai import router as local_ai_router
from features.search.router import route_query_intent
from features.search.service import hybrid_search
from features.slides import router as slides_router
from features.slides import service as slides_service
from features.tutor_agent import budget, key_verify
from features.tutor_agent.models_discovery import discover_models
from features.tutor_agent.providers import list_provider_models
from features.tutor_agent.service import ask_tutor as run_tutor
from features.tutor_agent.streaming import stream_messages_events, stream_tutor_events
from features.ui import (
    model_routes,
    public_config,
    public_rate_limit,
    selection,
    slides_source,
    ui_routers,
    work_bridge,
    workflow_bridge,
    workspace,
)
from features.ui.cloud_access import build_embedder, build_guard
from features.ui.hardware import hardware_advice
from features.ui.privacy import require_local
from features.ui.startup import area_lifespan
from features.ui.template import HTML_PAGE
from features.ui.upload_guard import upload_body_guard
from features.work_board import router as work_board_router
from features.work_board import service as work_board_service
from features.workflows import engine as workflow_engine
from features.workflows import router as workflow_router

STATIC_DIR, AUTO_EMBED = bundle_root() / "features" / "ui" / "static", os.environ.get("REALM_AUTO_EMBED", "1").strip().lower() not in {"0", "false", "no"}
secrets.load_dotenv_files()
WORKSPACE_CONFIG, INDEX, _INDEX_KEY = workspace.load_workspace_config(), [], None

def _load_area(target: Path) -> list[contracts.KnowledgeChunk]:
    cache = cache_index_for_dir(target, workspace.REPO_ROOT)
    if cache.is_symlink():
        raise HTTPException(status_code=400, detail="Area index cannot be a symbolic link")
    cached, meta = load_chunks_meta(cache) if cache.is_file() else ([], {})
    chunks = embedder.hydrate_embeddings(ingest_directory(target, read_only=target.resolve().parent != workspace.REPO_ROOT.resolve()), cached, embed_missing=AUTO_EMBED, cached_model=str(meta.get("embedding_model") or ""))
    save_chunks(chunks, cache, embedding_model=embedder.DEFAULT_EMBED_MODEL, embedding_provider="ollama")
    return chunks

def _reindex(target_dir: Path) -> list[contracts.KnowledgeChunk]:
    global INDEX, _INDEX_KEY
    INDEX = selection.merge(WORKSPACE_CONFIG, workspace.REPO_ROOT, _load_area) if len(WORKSPACE_CONFIG.active_dirs) > 1 else selection.filter_chunks(_load_area(target_dir), WORKSPACE_CONFIG.knowledge_dir, WORKSPACE_CONFIG)
    _INDEX_KEY = (str(workspace.REPO_ROOT), tuple(WORKSPACE_CONFIG.active_dirs), id(INDEX))
    return INDEX

def get_index() -> list[contracts.KnowledgeChunk]:
    with workspace.STATE_LOCK:
        if not WORKSPACE_CONFIG.active_dirs:
            return []
        if len(WORKSPACE_CONFIG.active_dirs) > 1:
            try:
                selection.paths(WORKSPACE_CONFIG, workspace.REPO_ROOT)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        if INDEX or _INDEX_KEY == (str(workspace.REPO_ROOT), tuple(WORKSPACE_CONFIG.active_dirs), id(INDEX)):
            return INDEX
        try:
            target = workspace.resolve_safe_knowledge_dir(WORKSPACE_CONFIG.knowledge_dir, create=False)
        except (HTTPException, ValueError):
            return []
        return _reindex(target)

def activate_workspace(config: contracts.WorkspaceConfig) -> dict[str, object]:
    global WORKSPACE_CONFIG, INDEX, _INDEX_KEY
    with workspace.STATE_LOCK:
        try:
            chunks = [] if not config.active_dirs else (selection.merge(config, workspace.REPO_ROOT, _load_area) if len(config.active_dirs) > 1 else selection.filter_chunks(_load_area(workspace.resolve_safe_knowledge_dir(config.knowledge_dir, create=True)), config.knowledge_dir, config))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        workspace.save_workspace_config(config)
        INDEX, WORKSPACE_CONFIG = chunks, config
        _INDEX_KEY = (str(workspace.REPO_ROOT), tuple(config.active_dirs), id(INDEX))
        return workspace.build_workspace_payload(config, chunks)


def _set_workspace_config(config: contracts.WorkspaceConfig) -> None:
    global WORKSPACE_CONFIG
    WORKSPACE_CONFIG = config
def _invalidate_index(_changes: dict[str, list[str]]) -> None:
    global INDEX, _INDEX_KEY
    with workspace.STATE_LOCK:
        INDEX, _INDEX_KEY = [], None
def build_public_app(data_dir: Path | None = None, quota_check: public_rate_limit.QuotaChecker | None = None) -> FastAPI:
    return public_config.build_public_fastapi(lambda d: ingest_directory(d, read_only=True), route_query_intent, hybrid_search, lambda *a, **kw: embed_text(*a, **kw), lambda *a, **kw: run_tutor(*a, skip_local_budget=True, public_mode=True, **kw), budget.estimate_usage, data_dir=data_dir, quota_check=quota_check)

def _build_local_app() -> FastAPI:
    cloud_guard = build_guard(lambda: WORKSPACE_CONFIG, budget.check_and_record_budget, budget.estimate_usage)
    wf_cbs = lambda cfg: workflow_bridge.build_workflow_callbacks(cfg, get_index, _reindex, hybrid_search, stream_messages_events, cloud_guard, slides_service.export_deck_bytes, work_board_service.add_tasks_from_text, impact_router.log_workflow_impact)  # noqa: E731
    local = FastAPI(title="REALM Engine", version=APP_VERSION, lifespan=area_lifespan(converters.repair_directory_topics, _invalidate_index, lambda: WORKSPACE_CONFIG, lambda: workflow_engine.tick_scheduled_workflows(WORKSPACE_CONFIG, wf_cbs(WORKSPACE_CONFIG), workspace.REPO_ROOT)))
    install_safe_error_handlers(local)
    local.add_middleware(upload_body_guard)
    local.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    deps: dict[str, object] = {
        "stream_messages": stream_messages_events, "reset_ollama": embedder.reset_ollama_status, "convert_bytes": converters.convert_bytes_to_markdown, "inspect_anon": inspect_anonymization, "anon_slug": anonymize_slug, "ingest_dir": ingest_directory, "route_intent": route_query_intent, "hybrid_search": hybrid_search, "embedder": build_embedder(lambda *a, **kw: embed_text(*a, **kw), cloud_guard), "run_tutor": lambda *args, **kwargs: run_tutor(*args, **kwargs), "stream_tutor": stream_tutor_events, "budget_snapshot": budget.budget_snapshot, "reset_budget": budget.reset_budget, "verify_key": key_verify.verify_provider_key,
    }
    routers = (
        *ui_routers.build_ui_routers(get_config=lambda: WORKSPACE_CONFIG, set_config=_set_workspace_config, activate_workspace=activate_workspace, get_index=get_index, reindex=_reindex, cloud_guard=cloud_guard, deps=deps),
        slides_router.build_router(slides_source.build_source_resolver(lambda: WORKSPACE_CONFIG, get_index)),
        work_board_router.build_router(lambda: WORKSPACE_CONFIG, work_bridge.build_work_source_resolver(lambda: WORKSPACE_CONFIG, get_index), stream_messages_events, work_bridge.build_work_vault_sync(lambda: WORKSPACE_CONFIG, _reindex), lambda: workspace.REPO_ROOT),
        impact_router.build_router(lambda: WORKSPACE_CONFIG, stream_messages_events, lambda a: work_board_service.project_name_map(a, workspace.REPO_ROOT), lambda: workspace.REPO_ROOT),
        focus_router.build_router(lambda: WORKSPACE_CONFIG, stream_messages_events, lambda a, lbl, mins, pid, tid, nt: impact_router.log_focus_time(a, workspace.REPO_ROOT, lbl, mins, pid, tid, nt), lambda a: work_board_service.open_task_summaries(a, workspace.REPO_ROOT), lambda a, blks: work_board_service.schedule_focus_events(a, list(blks), workspace.REPO_ROOT), lambda: workspace.REPO_ROOT),
        workflow_router.build_router(lambda: WORKSPACE_CONFIG, wf_cbs, lambda: workspace.REPO_ROOT),
        local_ai_router.build_router(lambda: workspace.REPO_ROOT),
    )
    for router in routers:
        local.include_router(router)
    local.add_api_route("/favicon.ico", lambda: FileResponse(STATIC_DIR / "favicon.ico"), methods=["GET"], include_in_schema=False)
    local.add_api_route("/healthz", lambda: {"status": "ok", "mode": "local", "version": APP_VERSION}, methods=["GET"])
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
