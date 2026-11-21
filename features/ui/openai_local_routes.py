"""Opt-in local OpenAI-compatible (/v1/models, /v1/chat/completions) API routes."""

import hmac
import os
import time
import uuid
from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request

from core.agent_personas import active_persona_prompt, list_agents
from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.net_security import is_loopback_ip
from core.retrieval_xray import build_retrieval_xray
from features.ui import workspace

_MAX_LOCAL_API_MSG_CHARS = 4000


def _local_api_enabled(cfg: WorkspaceConfig) -> bool:
    return bool(cfg.enable_local_api) or os.environ.get("REALM_ENABLE_LOCAL_API", "").strip() == "1"


def _is_loopback_client(host: str) -> bool:
    low = host.strip().lower()
    if low == "localhost" or is_loopback_ip(low):
        return True
    return low == "testclient" and bool(os.environ.get("PYTEST_CURRENT_TEST"))


def _require_local_api_access(request: Request, cfg: WorkspaceConfig) -> None:
    if not _local_api_enabled(cfg):
        raise HTTPException(status_code=403, detail="Local OpenAI-Compatible API is disabled. Enable it in Settings → AI & Voice.")
    client_host = request.client.host if request.client else ""
    if not client_host or not _is_loopback_client(client_host):
        raise HTTPException(status_code=403, detail="Local OpenAI-Compatible API accepts loopback requests only.")
    expected_token = os.environ.get("REALM_LOCAL_API_TOKEN", "").strip()
    if expected_token:
        auth = request.headers.get("authorization", "").strip()
        provided = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if not provided or not hmac.compare_digest(provided, expected_token):
            raise HTTPException(status_code=401, detail="Invalid or missing Bearer token for Local OpenAI API.")


def build_router(
    config: Callable[[], WorkspaceConfig],
    chunks: Callable[[], list[KnowledgeChunk]],
) -> APIRouter:
    router = APIRouter()

    @router.get("/v1/models")
    def openai_list_models(request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            _require_local_api_access(request, active)
            agents = list_agents(workspace.REPO_ROOT, active.agent_name)
        now = int(time.time())
        return {"object": "list", "data": [{"id": f"realm/{a.id}", "object": "model", "created": now, "owned_by": "realm-engine"} for a in agents]}

    @router.post("/v1/chat/completions")
    async def openai_chat_completions(request: Request) -> dict[str, object]:
        try:
            body = await request.json()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Provide a JSON object") from exc
        if not isinstance(body, dict):
            raise HTTPException(status_code=422, detail="Invalid OpenAI request payload")
        with workspace.STATE_LOCK:
            active = config()
            _require_local_api_access(request, active)
            model_spec = str(body.get("model") or f"realm/{active.active_agent}")
            agent_id = model_spec.split("/")[-1] if "/" in model_spec else active.active_agent
            agent, _ = active_persona_prompt(workspace.REPO_ROOT, agent_id, active.agent_name)
            cur_chunks = list(chunks())
        raw_messages = body.get("messages")
        messages: list[object] = list(raw_messages) if isinstance(raw_messages, list) else []
        user_msg = next((str(m.get("content") or "") for m in reversed(messages) if isinstance(m, dict) and m.get("role") == "user"), "").strip()[:_MAX_LOCAL_API_MSG_CHARS]
        if not user_msg:
            raise HTTPException(status_code=400, detail="Provide at least one user message")
        rows = build_retrieval_xray(user_msg, cur_chunks, top_k=3 if active.eco_mode else 5, retrieval_mode="lexical")
        answer = "\n\n".join(f"**{r['title']}**\n{r['snippet']}" for r in rows) if rows else "No matching passages found in the active REALM workspace."
        return {
            "id": f"chatcmpl-realm-{uuid.uuid4().hex[:10]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"realm/{agent.id}",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": f"[{agent.name}]\n\n{answer}"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": max(1, len(user_msg) // 4), "completion_tokens": max(1, len(answer) // 4), "total_tokens": max(2, (len(user_msg) + len(answer)) // 4)},
            "realm_sources": [{"doc_id": r["doc_id"], "title": r["title"], "rrf_score": r["rrf_score"]} for r in rows],
        }

    return router
