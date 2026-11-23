"""FastAPI HTTP + SSE router for the integrated local-only Bottom Panel Terminal."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from core.terminal_contracts import (
    TerminalCreateRequest,
    TerminalInputRequest,
    TerminalResizeRequest,
    TerminalSignalRequest,
)
from features.terminal import service


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _wait_chunks(entry: dict[str, Any], last_seq: int, timeout: float = 0.5) -> tuple[list[tuple[int, str]], bool]:
    cond = entry["cond"]
    with cond:
        chunks = [(s, txt) for s, txt in entry["history"] if s > last_seq]
        if chunks or entry["closed"]:
            return chunks, bool(entry["closed"])
        cond.wait(timeout=timeout)
        chunks = [(s, txt) for s, txt in entry["history"] if s > last_seq]
        return chunks, bool(entry["closed"])


def build_router(resolve_cwd: Callable[[], Path]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/terminal/sessions")
    def get_sessions() -> dict[str, object]:
        return {"sessions": [s.model_dump() for s in service.list_sessions()]}

    @router.post("/api/terminal/sessions")
    def start_session(body: TerminalCreateRequest | None = None) -> dict[str, object]:
        req = body or TerminalCreateRequest()
        try:
            info = service.create_session(resolve_cwd(), label=req.label, cols=req.cols, rows=req.rows)
        except OverflowError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"Could not start local shell: {exc}") from exc
        return {"session": info.model_dump()}

    @router.get("/api/terminal/sessions/{session_id}/stream")
    async def stream_session(session_id: str, request: Request, after: int = 0) -> StreamingResponse:
        entry = service.get_session_entry(session_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Terminal session not found")

        async def _gen() -> AsyncIterator[str]:
            last_seq, idle_ticks = max(0, int(after)), 0
            while True:
                if await request.is_disconnected():
                    return
                chunks, closed = await asyncio.to_thread(_wait_chunks, entry, last_seq, 0.5)
                if chunks:
                    idle_ticks = 0
                    for seq, text in chunks:
                        last_seq = seq
                        yield _sse("chunk", {"seq": seq, "data": text})
                else:
                    idle_ticks += 1
                    if idle_ticks >= 25:
                        idle_ticks = 0
                        yield ": keepalive\n\n"
                if closed:
                    code = entry["proc"].poll()
                    yield _sse("exit", {"exit_code": code})
                    return

        return StreamingResponse(
            _gen(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    @router.post("/api/terminal/sessions/{session_id}/input")
    def send_input(session_id: str, body: TerminalInputRequest) -> dict[str, object]:
        try:
            service.write_input(session_id, body.data)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Terminal session not found") from exc
        except OSError as exc:
            raise HTTPException(status_code=409, detail="Terminal process is no longer accepting input") from exc
        return {"ok": True}

    @router.post("/api/terminal/sessions/{session_id}/signal")
    def send_sig(session_id: str, body: TerminalSignalRequest) -> dict[str, object]:
        try:
            service.send_signal(session_id, body.signal)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Terminal session not found") from exc
        except OSError as exc:
            raise HTTPException(status_code=409, detail="Terminal process already exited") from exc
        return {"ok": True}

    @router.post("/api/terminal/sessions/{session_id}/resize")
    def resize(session_id: str, body: TerminalResizeRequest) -> dict[str, object]:
        try:
            service.resize_session(session_id, body.cols, body.rows)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Terminal session not found") from exc
        return {"ok": True}

    @router.delete("/api/terminal/sessions/{session_id}")
    def delete_session(session_id: str) -> dict[str, object]:
        if not service.close_session(session_id):
            raise HTTPException(status_code=404, detail="Terminal session not found")
        return {"deleted": True, "id": session_id}

    return router
