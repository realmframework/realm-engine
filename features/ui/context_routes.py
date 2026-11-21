"""Routes for Context Meter, Context Compaction, Clear Context, Mid-Chat Vault Attach & Synthesis."""

import json
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from core import context_meter
from core.cancellation import begin_request, check_cancelled, end_request
from core.contracts import ChatTurn, TutorResponse, WorkspaceConfig
from core.output_formats import build_format_instruction, get_format
from features.ui import chat_store, workspace
from features.ui.privacy import require_local

StreamMsgFn = Callable[..., AsyncIterator[dict[str, object]]]


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _resolve_chat_path(active: WorkspaceConfig, free_chat: bool) -> tuple[str, list[str]]:
    return (chat_store.FREE_CHAT_AREA, [chat_store.FREE_CHAT_AREA]) if free_chat else (active.knowledge_dir, active.active_dirs)


def build_router(config: Callable[[], WorkspaceConfig], stream_messages: StreamMsgFn | None = None) -> APIRouter:
    router = APIRouter()

    @router.get("/api/chats/{chat_id}/context")
    def get_context(chat_id: str, provider: str = "ollama", model: str = "qwen3:8b", free_chat: bool = False) -> dict[str, object]:
        with workspace.STATE_LOCK:
            area, _ = _resolve_chat_path(config(), free_chat)
            session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(area))
            notes = [{"name": n["name"], "chars": len(n["content"])} for n in session.attached_notes] if session else []
            return {"context_usage": context_meter.compute_context_usage(session, provider, model), "attached_notes": notes, "compacted_summary": session.compacted_summary if session else ""}

    @router.post("/api/chats/{chat_id}/clear-context")
    async def clear_context(chat_id: str, request: Request) -> dict[str, object]:
        body = await request.json() if "application/json" in request.headers.get("content-type", "") else {}
        free_chat = bool(body.get("free_chat")) if isinstance(body, dict) else False
        provider = str(body.get("provider") or "ollama") if isinstance(body, dict) else "ollama"
        model = str(body.get("model") or "qwen3:8b") if isinstance(body, dict) else "qwen3:8b"
        with workspace.STATE_LOCK:
            area, _ = _resolve_chat_path(config(), free_chat)
            path = chat_store.area_chat_path(area)
            session = chat_store.get_chat_session(chat_id, path)
            if session is None:
                raise HTTPException(status_code=404, detail="Chat session not found")
            updated = chat_store.save_chat_session(session.model_copy(update={"compacted_summary": "", "context_cleared_at": len(session.turns)}), path)
            return {"session": updated.model_dump(), "context_usage": context_meter.compute_context_usage(updated, provider, model)}

    @router.post("/api/chats/{chat_id}/compact")
    async def compact_context(chat_id: str, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        body = await request.json() if "application/json" in request.headers.get("content-type", "") else {}
        free_chat = bool(body.get("free_chat")) if isinstance(body, dict) else False
        provider = str(body.get("provider") or "ollama") if isinstance(body, dict) else "ollama"
        model = str(body.get("model") or "qwen3:8b") if isinstance(body, dict) else "qwen3:8b"
        api_key = x_api_key or (str(body.get("api_key") or "") if isinstance(body, dict) else "")
        with workspace.STATE_LOCK:
            active = config()
            require_local(active, provider, model)
            area, _ = _resolve_chat_path(active, free_chat)
            path = chat_store.area_chat_path(area)
            session = chat_store.get_chat_session(chat_id, path)
            if session is None or not session.turns:
                raise HTTPException(status_code=400, detail="Nothing to compress yet in this chat.")
            messages = context_meter.build_compaction_messages(session, active.language)
            t_cfg = workspace.build_tutor_config(provider, model, api_key or None, 0.1).model_copy(
                update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language}
            )
        parts: list[str] = []
        if stream_messages is not None:
            async for ev in stream_messages(messages, t_cfg, temperature=0.1, max_tokens=700):
                if ev.get("type") == "token" and ev.get("delta"):
                    parts.append(str(ev["delta"]))
        summary = "".join(parts).strip()
        if not summary:
            summary = "\n".join(f"- {t.query[:120]}: {(t.tutor.answer[:160] if t.tutor else '')}" for t in session.turns[-6:])
        with workspace.STATE_LOCK:
            latest = chat_store.get_chat_session(chat_id, path) or session
            keep_from = max(0, len(latest.turns) - 2)
            updated = chat_store.save_chat_session(latest.model_copy(update={"compacted_summary": summary, "context_cleared_at": keep_from}), path)
            return {"session": updated.model_dump(), "summary": summary, "context_usage": context_meter.compute_context_usage(updated, provider, model)}

    @router.post("/api/chats/{chat_id}/synthesize")
    async def synthesize_format(chat_id: str, request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> StreamingResponse:
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Provide a JSON object")
        fmt = get_format(workspace.REPO_ROOT, str(body.get("format_id") or ""))
        if fmt is None:
            raise HTTPException(status_code=404, detail="Output format not found")
        free_chat = bool(body.get("free_chat"))
        extra_note = str(body.get("extra_instruction") or "").strip()
        provider = str(body.get("provider") or "ollama")
        model = str(body.get("model") or "qwen3:8b")
        api_key = x_api_key or str(body.get("api_key") or "")
        with workspace.STATE_LOCK:
            active = config()
            require_local(active, provider, model)
            area, dirs = _resolve_chat_path(active, free_chat)
            path = chat_store.area_chat_path(area)
            session = chat_store.get_chat_session(chat_id, path)
            if session is None or (not session.turns and not session.attached_notes):
                raise HTTPException(status_code=400, detail="Have at least one message or attached note before synthesizing a format.")
            summary, history, notes = context_meter.active_history_for_session(session)
            t_cfg = workspace.build_tutor_config(provider, model, api_key or None, 0.2).model_copy(
                update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language}
            )
            cited = list(dict.fromkeys(c for t in session.turns if t.tutor for c in t.tutor.cited_titles))[:8]
        instruction = build_format_instruction(fmt, extra_note)
        prompt_parts = [f"Compacted memory:\n{summary}"] if summary else []
        prompt_parts.extend(f"Turn {i} User: {q}\nAssistant: {a}" for i, (q, a) in enumerate(history, 1))
        prompt_parts.extend(f"Attached File ({n['name']}):\n{n['content'][:10000]}" for n in notes[-6:])
        messages = [{"role": "system", "content": instruction}, {"role": "user", "content": "\n\n".join(prompt_parts)}]

        async def _gen() -> AsyncIterator[str]:
            token = begin_request(x_request_id)
            emitted, thought, meta = [], [], {}
            try:
                if stream_messages is not None:
                    async for ev in stream_messages(messages, t_cfg, temperature=0.2, request_id=x_request_id, max_tokens=3072):
                        check_cancelled()
                        et = ev.get("type")
                        if et == "thinking" and ev.get("delta"):
                            thought.append(str(ev["delta"]))
                            yield _sse("thinking", {"delta": str(ev["delta"])})
                        elif et == "token" and ev.get("delta"):
                            emitted.append(str(ev["delta"]))
                            yield _sse("token", {"delta": str(ev["delta"])})
                        elif et == "meta":
                            meta = dict(ev)
                answer_text = "".join(emitted).strip() or f"# {fmt.name}\n\nNo content generated."
                turn = ChatTurn(query=f"Synthesize as {fmt.name}" + (f" — {extra_note}" if extra_note else ""), ask_tutor=True, tutor=TutorResponse(answer=answer_text, cited_titles=cited, knowledge_gap_detected=False, recommended_topics=[]), results=[], created_at=chat_store.utc_now_iso(), thinking="".join(thought).strip(), telemetry=meta, format_name=fmt.name)
                with workspace.STATE_LOCK:
                    updated = chat_store.append_chat_turn(chat_id, turn, path, area, dirs)
                ctx_usage = context_meter.compute_context_usage(updated, provider, model)
                yield _sse("telemetry", {**meta, "context_usage": ctx_usage})
                yield _sse("done", {**updated.model_dump(), "context_usage": ctx_usage})
            except InterruptedError:
                yield _sse("stopped", {"partial": "".join(emitted).strip()})
            finally:
                end_request(x_request_id, token)

        return StreamingResponse(_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return router
