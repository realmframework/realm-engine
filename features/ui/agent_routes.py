"""Routes for the REALM Agent Team (persona.md selection, editing, creation & folder reveal)."""

import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core import agent_personas
from core.agent_presets import BUILTIN_AGENTS
from core.contracts import WorkspaceConfig
from core.persona_codec import render_persona_md
from features.ui import workspace


def _open_dir_in_os(target: Path) -> None:
    if sys.platform == "darwin":
        subprocess.Popen(["open", str(target)])
    elif sys.platform == "win32":
        subprocess.Popen(["explorer", str(target)])
    else:
        subprocess.Popen(["xdg-open", str(target)])


async def _read_json(request: Request) -> dict[str, object]:
    try:
        body = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Provide valid JSON") from exc
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Provide a JSON object")
    return body


def _serialize_team(cfg: WorkspaceConfig) -> dict[str, object]:
    agents = agent_personas.list_agents(workspace.REPO_ROOT, saga_name_override=cfg.agent_name)
    ids = {a.id for a in agents}
    active_id = cfg.active_agent if cfg.active_agent in ids else (agents[0].id if agents else "saga")
    return {
        "agents": [{**a.model_dump(), "raw_markdown": render_persona_md(a)} for a in agents],
        "active_agent": active_id,
        "sync_agent_palette": cfg.sync_agent_palette,
        "agents_dir": str(agent_personas.agents_root(workspace.REPO_ROOT)),
        "has_missing_defaults": any(b.id not in ids for b in BUILTIN_AGENTS),
    }


def build_router(get_config: Callable[[], WorkspaceConfig], set_config: Callable[[WorkspaceConfig], None]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/agents")
    def get_agents() -> dict[str, object]:
        with workspace.STATE_LOCK:
            return _serialize_team(get_config())

    @router.post("/api/agents/select")
    async def select_agent(request: Request) -> dict[str, object]:
        body = await _read_json(request)

        def _apply() -> dict[str, object]:
            with workspace.STATE_LOCK:
                cfg = get_config()
                updates: dict[str, object] = {}
                if body.get("agent_id"):
                    updates["active_agent"] = agent_personas.get_agent(workspace.REPO_ROOT, str(body["agent_id"]), cfg.agent_name).id
                if "sync_agent_palette" in body:
                    updates["sync_agent_palette"] = bool(body["sync_agent_palette"])
                updated = cfg.model_copy(update=updates) if updates else cfg
                workspace.save_workspace_config(updated)
                set_config(updated)
                return {**_serialize_team(updated), "config": updated.model_dump()}

        return await run_in_threadpool(_apply)

    @router.post("/api/agents")
    async def upsert_agent(request: Request) -> dict[str, object]:
        body = await _read_json(request)

        def _save() -> dict[str, object]:
            try:
                raw_temp = body.get("temperature")
                temp_val = float(str(raw_temp)) if raw_temp is not None else 0.2
                with workspace.STATE_LOCK:
                    saved = agent_personas.save_agent(
                        workspace.REPO_ROOT,
                        name=str(body.get("name") or ""), role=str(body.get("role") or "Specialist"),
                        tagline=str(body.get("tagline") or ""), palette=str(body.get("palette") or "realm"),
                        default_format=str(body.get("default_format") or ""), model_provider=str(body.get("model_provider") or ""),
                        model_name=str(body.get("model_name") or ""), temperature=temp_val,
                        instructions=str(body.get("instructions") or ""), agent_id=str(body.get("id") or ""),
                        raw_markdown=str(body.get("raw_markdown") or ""),
                    )
                    cfg = get_config()
                    if saved.id == "saga" and saved.name != cfg.agent_name:
                        cfg = cfg.model_copy(update={"agent_name": saved.name})
                        workspace.save_workspace_config(cfg)
                        set_config(cfg)
                    return {"agent": {**saved.model_dump(), "raw_markdown": render_persona_md(saved)}, **_serialize_team(cfg)}
            except (ValueError, TypeError) as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        return await run_in_threadpool(_save)

    @router.delete("/api/agents/{agent_id}")
    def remove_agent(agent_id: str) -> dict[str, object]:
        try:
            with workspace.STATE_LOCK:
                deleted = agent_personas.delete_agent(workspace.REPO_ROOT, agent_id)
                cfg = get_config()
                remaining = agent_personas.list_agents(workspace.REPO_ROOT, cfg.agent_name)
                if cfg.active_agent not in {a.id for a in remaining} and remaining:
                    cfg = cfg.model_copy(update={"active_agent": remaining[0].id})
                    workspace.save_workspace_config(cfg)
                    set_config(cfg)
                return {"deleted": deleted, **_serialize_team(cfg)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/agents/{agent_id}/reset")
    def reset_builtin_agent(agent_id: str) -> dict[str, object]:
        try:
            with workspace.STATE_LOCK:
                restored = agent_personas.reset_agent(workspace.REPO_ROOT, agent_id)
                cfg = get_config()
                if restored.id == "saga" and cfg.agent_name != "Saga":
                    cfg = cfg.model_copy(update={"agent_name": "Saga"})
                    workspace.save_workspace_config(cfg)
                    set_config(cfg)
                return {"agent": {**restored.model_dump(), "raw_markdown": render_persona_md(restored)}, **_serialize_team(cfg)}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/api/agents/restore-defaults")
    def restore_defaults() -> dict[str, object]:
        with workspace.STATE_LOCK:
            agent_personas.restore_default_team(workspace.REPO_ROOT)
            return _serialize_team(get_config())

    @router.post("/api/agents/reveal-folder")
    def reveal_agents_folder() -> dict[str, object]:
        folder = agent_personas.seed_default_agents(workspace.REPO_ROOT)
        try:
            _open_dir_in_os(folder)
        except OSError as exc:
            raise HTTPException(status_code=500, detail="Could not open agents folder") from exc
        return {"opened": True, "path": str(folder)}

    return router
