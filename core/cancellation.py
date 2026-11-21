"""Cooperative and socket-level request cancellation for in-flight AI generations."""

import asyncio
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from contextvars import ContextVar, Token
from threading import Event, Lock
from typing import Any

import httpx

from core.runtime import is_loopback_url

_LOCK = Lock()
_ACTIVE: dict[str, list[Any]] = {}
_EARLY_CANCELLED: dict[str, float] = {}
_EARLY_TTL_SEC, _MAX_EARLY = 15.0, 256
_CURRENT_REQUEST_ID: ContextVar[str | None] = ContextVar("realm_request_id", default=None)
_ORIG_HTTPX_POST = httpx.post


def _prune_early(now: float) -> None:
    for key in [k for k, exp in _EARLY_CANCELLED.items() if exp <= now]:
        _EARLY_CANCELLED.pop(key, None)

def begin_request(request_id: str | None) -> Token[str | None]:
    """Register a cancellable request ID for the current execution context (ref-counted)."""
    clean = (request_id or "").strip()[:128]
    if not clean:
        return _CURRENT_REQUEST_ID.set(None)
    now = time.monotonic()
    with _LOCK:
        _prune_early(now)
        pre_cancelled = _EARLY_CANCELLED.pop(clean, 0.0) > now
        if clean in _ACTIVE:
            _ACTIVE[clean][2] += 1
            if pre_cancelled:
                _ACTIVE[clean][0].set()
        else:
            ev = Event()
            if pre_cancelled:
                ev.set()
            _ACTIVE[clean] = [ev, [], 1]
    return _CURRENT_REQUEST_ID.set(clean)

def end_request(request_id: str | None, token: Token[str | None]) -> None:
    """Unregister a request ID (decrementing ref-count) and restore the context variable."""
    if clean := (request_id or "").strip()[:128]:
        with _LOCK:
            if entry := _ACTIVE.get(clean):
                entry[2] -= 1
                if entry[2] <= 0:
                    _ACTIVE.pop(clean, None)
    _CURRENT_REQUEST_ID.reset(token)


def cancel_request(request_id: str) -> bool:
    """Cancel an in-flight request and tear down any registered upstream network operations."""
    clean = request_id.strip()[:128]
    if not clean:
        return False
    now = time.monotonic()
    with _LOCK:
        entry = _ACTIVE.get(clean)
        if entry is None:
            _prune_early(now)
            if len(_EARLY_CANCELLED) >= _MAX_EARLY:
                _EARLY_CANCELLED.pop(next(iter(_EARLY_CANCELLED)), None)
            _EARLY_CANCELLED[clean] = now + _EARLY_TTL_SEC
            return False
        entry[0].set()
        snapshot = list(entry[1])
    for closer in snapshot:
        with suppress(RuntimeError, OSError):
            closer()
    return True


def check_cancelled() -> None:
    """Raise InterruptedError if the active request has been cancelled."""
    if not (req_id := _CURRENT_REQUEST_ID.get()):
        return
    with _LOCK:
        entry = _ACTIVE.get(req_id)
        cancelled = entry is not None and entry[0].is_set()
    if cancelled:
        raise InterruptedError("Generation stopped by user.")


def _attach_closer(req_id: str, closer: Callable[[], None]) -> None:
    with _LOCK:
        if (entry := _ACTIVE.get(req_id)) is None:
            return
        if entry[0].is_set():
            raise InterruptedError("Generation stopped by user.")
        entry[1].append(closer)


def _detach_closer(req_id: str, closer: Callable[[], None]) -> None:
    with _LOCK:
        if (entry := _ACTIVE.get(req_id)) is not None and closer in entry[1]:
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


def _run_async_post(req_id: str | None, url: str, payload: dict[str, Any], headers: dict[str, str] | None, timeout: float) -> Any:
    async def _send() -> Any:
        detach = attach_current_task(req_id)
        try:
            async with httpx.AsyncClient(timeout=timeout, trust_env=not is_loopback_url(url)) as client:
                return await client.post(url=url, json=payload, headers=headers)
        except asyncio.CancelledError as exc:
            raise InterruptedError("Generation stopped by user.") from exc
        finally:
            detach()

    return asyncio.run(_send())


def post_cancellable(url: str, payload: dict[str, Any], headers: dict[str, str] | None = None, timeout: float = 30.0) -> Any:
    """Execute an HTTP POST that immediately closes its TCP socket if cancelled."""
    check_cancelled()
    req_id = _CURRENT_REQUEST_ID.get()
    if httpx.post is not _ORIG_HTTPX_POST:
        return httpx.post(url=url, json=payload, headers=headers, timeout=timeout) if headers is not None else httpx.post(url=url, json=payload, timeout=timeout)
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _run_async_post(req_id, url, payload, headers, timeout)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_run_async_post, req_id, url, payload, headers, timeout).result()
