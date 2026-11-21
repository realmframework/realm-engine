"""Aggregate UI-local FastAPI routers so app.py stays concise as the composition root."""

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter

from core import contracts
from features.ui import (
    agent_builder_routes,
    appearance_routes,
    area_routes,
    audio_routes,
    backup_routes,
    budget_routes,
    chat_routes,
    compliance_routes,
    document_routes,
    model_routes,
    power_routes,
    query_routes,
    study_routes,
    workspace_templates,
)


def build_ui_routers(
    *,
    get_config: Callable[[], contracts.WorkspaceConfig],
    set_config: Callable[[contracts.WorkspaceConfig], None],
    activate_workspace: Callable[[contracts.WorkspaceConfig], dict[str, object]],
    get_index: Callable[[], list[contracts.KnowledgeChunk]],
    reindex: Callable[[Path], list[contracts.KnowledgeChunk]],
    cloud_guard: object,
    deps: dict[str, object],
) -> tuple[APIRouter, ...]:
    audio_routes.privacy_config, audio_routes.cloud_admission = get_config, cloud_guard  # type: ignore[assignment]
    return (
        appearance_routes.build_router(get_config, set_config),
        agent_builder_routes.build_router(get_config, deps["stream_messages"]),  # type: ignore[arg-type]
        backup_routes.build_router(get_config, activate_workspace),
        workspace_templates.build_router(get_config, activate_workspace),
        model_routes.build_router(get_config, deps["reset_ollama"]),  # type: ignore[arg-type]
        audio_routes.router,
        chat_routes.build_router(get_config, deps["convert_bytes"], deps["stream_messages"], deps["inspect_anon"]),  # type: ignore[arg-type]
        document_routes.build_router(get_config, reindex, deps["convert_bytes"], deps["inspect_anon"], deps["anon_slug"]),  # type: ignore[arg-type]
        area_routes.build_router(get_config, activate_workspace, get_index, deps["ingest_dir"]),  # type: ignore[arg-type]
        query_routes.build_router(get_config, get_index, deps["route_intent"], deps["hybrid_search"], deps["embedder"], deps["run_tutor"], deps["stream_tutor"]),  # type: ignore[arg-type]
        compliance_routes.build_router(get_config, get_index, reindex, deps["inspect_anon"], deps["hybrid_search"]),  # type: ignore[arg-type]
        budget_routes.build_router(get_config, deps["budget_snapshot"], deps["reset_budget"], deps["verify_key"]),  # type: ignore[arg-type]
        power_routes.build_router(get_config, get_index, reindex),
        study_routes.build_router(get_config, get_index, deps["stream_messages"]),  # type: ignore[arg-type]
    )
