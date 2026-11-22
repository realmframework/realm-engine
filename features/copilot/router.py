"""FastAPI SSE streaming router for the Right Sidebar Context-Aware REALM Copilot."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse

from core.ai_stream import (
    StreamMessagesFn,
    build_workspace_tutor_config,
    require_local_policy,
)
from core.contracts import WorkspaceConfig
from core.copilot_contracts import CopilotChatRequest
from features.copilot import service


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def build_router(
    get_config: Callable[[], WorkspaceConfig],
    stream_messages: StreamMessagesFn,
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/copilot/chat/stream")
    async def copilot_chat_stream(
        request: Request,
        body: CopilotChatRequest,
        x_api_key: str | None = Header(default=None, alias="x-api-key"),
    ) -> StreamingResponse:
        cfg = get_config()
        require_local_policy(cfg, body.provider, body.model)
        api_key = x_api_key or body.api_key
        tcfg = build_workspace_tutor_config(cfg, body.provider, body.model or "", api_key, temperature=0.25)
        prompt_msgs = service.build_copilot_messages(body, cfg.language, cfg.agent_name or "Saga")

        async def _gen() -> AsyncIterator[str]:
            raw_buf = ""
            emitted_len = 0
            in_action = False
            try:
                async for ev in stream_messages(prompt_msgs, tcfg, temperature=0.25, max_tokens=2200):
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
                yield _sse("done", {"reply": reply, "actions": [a.model_dump() for a in actions]})
            except Exception as exc:
                yield _sse("error", {"detail": str(exc) or "Copilot request failed"})

        return StreamingResponse(
            _gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    return router
