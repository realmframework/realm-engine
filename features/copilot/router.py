"""FastAPI SSE streaming router for the Right Sidebar Context-Aware REALM Copilot."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import cast

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from core import model_routing
from core.agent_personas import active_persona_prompt
from core.ai_stream import (
    StreamMessagesFn,
    build_workspace_tutor_config,
    require_local_policy,
)
from core.contracts import ProviderName, WorkspaceConfig
from core.copilot_contracts import CopilotChatRequest
from core.output_formats import build_format_instruction, get_format
from features.copilot import service


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _assert_copilot_scope(cfg: WorkspaceConfig, request: Request, body: CopilotChatRequest) -> None:
    expected = request.headers.get("x-knowledge-area")
    if expected is not None and expected != cfg.knowledge_dir:
        raise HTTPException(status_code=409, detail="Knowledge area changed. Refresh before continuing.")
    for raw_id in (body.context.doc_id, *(f.doc_id for f in body.context.extra_files)):
        if not raw_id:
            continue
        area, local = raw_id.split("::", 1) if "::" in raw_id else (cfg.knowledge_dir, raw_id)
        excluded = {p.strip("/").casefold() for p in cfg.excluded_subfolders.get(area, []) if p.strip("/")}
        rel = local.strip("/").casefold()
        if any(rel == ex or rel.startswith(ex + "/") for ex in excluded):
            raise HTTPException(status_code=403, detail="Excluded folder content cannot be sent to Copilot.")


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    stream_messages: StreamMessagesFn,
    get_data_root: Callable[[], Path] | None = None,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/copilot/chat/stream")
    async def copilot_chat_stream(
        request: Request,
        body: CopilotChatRequest,
        x_api_key: str | None = Header(default=None, alias="x-api-key"),
    ) -> StreamingResponse:
        cfg = get_config()
        _assert_copilot_scope(cfg, request, body)
        root = get_data_root() if get_data_root is not None else Path.cwd()
        api_key = x_api_key or body.api_key
        agent, persona_instr = await asyncio.to_thread(
            active_persona_prompt, root, body.agent_id or cfg.active_agent, cfg.agent_name
        )
        eff_prov, eff_model, eff_key, is_pinned, _notice = await asyncio.to_thread(
            model_routing.resolve_agent_model, agent, cfg, body.provider, body.model, api_key
        )
        require_local_policy(cfg, eff_prov, eff_model)
        fmt = await asyncio.to_thread(get_format, root, body.format_id or "") if body.format_id else None
        fmt_instr = build_format_instruction(fmt) if fmt else ""
        eff_temp = max(0.0, min(1.0, float(agent.temperature)))
        eff_provider = cast(ProviderName, eff_prov)
        tcfg = build_workspace_tutor_config(cfg, eff_provider, eff_model, eff_key, temperature=eff_temp)
        prompt_msgs = service.build_copilot_messages(
            body, cfg.language, agent.name, persona_instr, fmt_instr
        )
        run_meta: dict[str, object] = {
            "agent_id": agent.id,
            "agent_name": agent.name,
            "provider": eff_prov,
            "model": eff_model or tcfg.model,
            "model_pinned": is_pinned,
            "format_id": fmt.id if fmt else "",
            "format_name": fmt.name if fmt else "",
        }

        async def _gen() -> AsyncIterator[str]:
            raw_buf = ""
            emitted_len = 0
            in_action = False
            try:
                await asyncio.to_thread(model_routing.maybe_unload_previous_ollama, eff_prov, eff_model or "")
                yield _sse("meta", run_meta)
                async for ev in stream_messages(prompt_msgs, tcfg, temperature=eff_temp, max_tokens=2200):
                    if await request.is_disconnected():
                        return
                    ev_type = str(ev.get("type") or "")
                    if ev_type == "error":
                        yield _sse("error", {"detail": str(ev.get("detail") or "Copilot provider error")})
                        return
                    if ev_type == "thinking" and ev.get("delta"):
                        yield _sse("thinking", {"delta": str(ev["delta"])})
                    elif ev_type == "token" and ev.get("delta"):
                        raw_buf += str(ev["delta"])
                        if not in_action:
                            tail = raw_buf[emitted_len:]
                            pos = tail.lower().find(service.ACTION_TAG_OPEN)
                            if pos >= 0:
                                if pos > 0:
                                    yield _sse("token", {"delta": tail[:pos]})
                                emitted_len += pos
                                in_action = True
                            else:
                                safe_end = max(emitted_len, len(raw_buf) - len(service.ACTION_TAG_OPEN))
                                if safe_end > emitted_len:
                                    yield _sse("token", {"delta": raw_buf[emitted_len:safe_end]})
                                    emitted_len = safe_end
                if not in_action and emitted_len < len(raw_buf):
                    yield _sse("token", {"delta": raw_buf[emitted_len:]})
                reply, actions = service.parse_copilot_response(raw_buf, body.context)
                yield _sse("done", {"reply": reply, "actions": [a.model_dump() for a in actions], "meta": run_meta})
            except Exception as exc:
                yield _sse("error", {"detail": str(exc) or "Copilot request failed"})

        return StreamingResponse(
            _gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    return router
