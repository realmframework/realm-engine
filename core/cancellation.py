"""Cooperative and socket-level request cancellation for in-flight AI generations."""

import asyncio
from collections.abc import Callable
from contextlib import suppress
from contextvars import ContextVar, Token
from threading import Event, Lock
from typing import Any

import httpx

_LOCK = Lock()
_ACTIVE: dict[str, tuple[Event, list[Callable[[], None]]]] = {}
_CURRENT_REQUEST_ID: ContextVar[str | None] = ContextVar("realm_request_id", default=None)
_ORIG_HTTPX_POST = httpx.post


def begin_request(request_id: str | None) -> Token[str | None]:
    """Register a cancellable request ID for the current execution context."""
    clean = (request_id or "").strip()[:128]
    if not clean:
        return _CURRENT_REQUEST_ID.set(None)
    with _LOCK:
        _ACTIVE.setdefault(clean, (Event(), []))
    return _CURRENT_REQUEST_ID.set(clean)


def end_request(request_id: str | None, token: Token[str | None]) -> None:
    """Unregister a request ID and restore the previous context variable."""
    clean = (request_id or "").strip()[:128]
    if clean:
        with _LOCK:
            _ACTIVE.pop(clean, None)
    _CURRENT_REQUEST_ID.reset(token)


def cancel_request(request_id: str) -> bool:
    """Cancel an in-flight request and close any registered upstream network operations."""
    clean = request_id.strip()[:128]
    if not clean:
        return False
    with _LOCK:
        entry = _ACTIVE.get(clean)
        if entry is None:
            return False
        event, closers = entry
        event.set()
        snapshot = list(closers)
    for closer in snapshot:
        with suppress(RuntimeError, OSError):
            closer()
    return True


def check_cancelled() -> None:
    """Raise InterruptedError if the active request has been cancelled."""
    req_id = _CURRENT_REQUEST_ID.get()
    if not req_id:
        return
    with _LOCK:
        entry = _ACTIVE.get(req_id)
        cancelled = entry is not None and entry[0].is_set()
    if cancelled:
        raise InterruptedError("Generation stopped by user.")


def _attach_closer(req_id: str, closer: Callable[[], None]) -> None:
    with _LOCK:
        entry = _ACTIVE.get(req_id)
        if entry is None:
            return
        if entry[0].is_set():
            raise InterruptedError("Generation stopped by user.")
        entry[1].append(closer)


def _detach_closer(req_id: str, closer: Callable[[], None]) -> None:
    with _LOCK:
        entry = _ACTIVE.get(req_id)
        if entry is not None and closer in entry[1]:
            entry[1].remove(closer)


def attach_current_task(req_id: str | None = None) -> Callable[[], None]:
    """Attach the active asyncio task to request cancellation and return a detach callback."""
    active_id = (req_id or _CURRENT_REQUEST_ID.get() or "").strip()[:128]
    task = asyncio.current_task()
    if not active_id or task is None:
        return lambda: None
    loop = asyncio.get_running_loop()

    def _abort() -> None:
        with suppress(RuntimeError):
            loop.call_soon_threadsafe(task.cancel)

    _attach_closer(active_id, _abort)
    return lambda: _detach_closer(active_id, _abort)


def post_cancellable(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
) -> Any:
    """Execute an HTTP POST that immediately tears down its TCP socket if cancelled."""
    check_cancelled()
    req_id = _CURRENT_REQUEST_ID.get()
    if not req_id or httpx.post is not _ORIG_HTTPX_POST:
        if headers is not None:
            return httpx.post(url=url, json=payload, headers=headers, timeout=timeout)
        return httpx.post(url=url, json=payload, timeout=timeout)

    async def _send() -> httpx.Response:
        loop = asyncio.get_running_loop()
        task = asyncio.current_task()
        if task is None:
            raise InterruptedError("Generation stopped by user.")

        def _abort() -> None:
            with suppress(RuntimeError):
                loop.call_soon_threadsafe(task.cancel)

        _attach_closer(req_id, _abort)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if headers is not None:
                    return await client.post(url=url, json=payload, headers=headers)
                return await client.post(url=url, json=payload)
        finally:
            _detach_closer(req_id, _abort)

    try:
        return asyncio.run(_send())
    except asyncio.CancelledError as exc:
        raise InterruptedError("Generation stopped by user.") from exc
