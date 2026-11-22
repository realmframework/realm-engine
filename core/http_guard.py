"""HTTP security headers and loopback Host/Origin/Referer/Sec-Fetch-Site/CSRF guards."""

import os
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import Scope

_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_MUTATING_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})
_UNIQUE_HEADERS = (b"host", b"origin", b"sec-fetch-site", b"content-length")
_MULTIPART_PATHS = frozenset({"/api/upload", "/api/backup/import", "/api/workspace/logo", "/api/anonymize/preview", "/api/audio/transcribe"})
_BASE_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
)
_LOCAL_EMBED_BASE_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"SAMEORIGIN"),
    (b"referrer-policy", b"no-referrer"),
)
_LOCAL_CSP = (
    b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    b"img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; font-src 'self' data:; "
    b"object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
)
_LOCAL_UI_CSP = (
    b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
    b"img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; font-src 'self' data:; "
    b"frame-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'"
)
_LOCAL_EXTRA_HEADERS = (
    (b"content-security-policy", _LOCAL_CSP),
    (b"cross-origin-resource-policy", b"same-origin"),
    (b"cross-origin-opener-policy", b"same-origin"),
)
_LOCAL_UI_EXTRA_HEADERS = (
    (b"content-security-policy", _LOCAL_UI_CSP),
    (b"cross-origin-resource-policy", b"same-origin"),
    (b"cross-origin-opener-policy", b"same-origin"),
)


def collect_headers(scope: Scope) -> tuple[dict[bytes, bytes], bool]:
    """Build lowercase header map and flag duplicate security-sensitive headers."""
    grouped: dict[bytes, list[bytes]] = {}
    for key, val in scope.get("headers", []):
        grouped.setdefault(key.lower(), []).append(val)
    has_dup = any(len(grouped.get(k, [])) > 1 for k in _UNIQUE_HEADERS)
    return {k: vals[0] for k, vals in grouped.items()}, has_dup


def _is_multipart_allowed(path: str) -> bool:
    return path in _MULTIPART_PATHS or (path.startswith("/api/chats/") and path.endswith("/attach"))


def _origin_matches_local(raw: str, raw_host: str, is_testclient: bool) -> bool:
    if raw.lower() == "null":
        return False
    parsed = urlparse(raw)
    orig_host = (parsed.hostname or "").strip("[]").lower()
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if raw_host and parsed.netloc.lower() != raw_host:
        return False
    return orig_host in _LOCAL_HOSTS or (is_testclient and orig_host == "testserver")


def validate_local_request(scope: Scope, headers: dict[bytes, bytes], has_dup: bool) -> tuple[int, str] | None:
    """Enforce strict loopback Host, Origin/Referer, Sec-Fetch-Site, and CSRF Content-Type rules."""
    if has_dup:
        return 400, "Duplicate security-sensitive header rejected."
    raw_host = headers.get(b"host", b"").decode("latin-1").strip().lower()
    client = scope.get("client")
    is_testclient = bool(client and str(client[0]) == "testclient" and os.environ.get("PYTEST_CURRENT_TEST"))
    if not raw_host:
        return 403, "Missing Host header for local server."
    parsed_host = urlparse(f"http://{raw_host}")
    try:
        _ = parsed_host.port
    except ValueError:
        return 403, "Invalid Host header for local server."
    host_name = (parsed_host.hostname or "").strip("[]").lower()
    if (
        parsed_host.username
        or parsed_host.password
        or parsed_host.path
        or parsed_host.query
        or parsed_host.fragment
        or (host_name not in _LOCAL_HOSTS and not (is_testclient and host_name == "testserver"))
    ):
        return 403, "Invalid Host header for local server."

    path = str(scope.get("path", ""))
    method = str(scope.get("method", "GET")).upper()
    sec_fetch = headers.get(b"sec-fetch-site", b"").decode("latin-1").strip().lower()
    if sec_fetch == "cross-site" and (method in _MUTATING_METHODS or path.startswith(("/api/", "/v1/"))):
        return 403, "Cross-site requests to the local server are blocked."
    if method not in _MUTATING_METHODS:
        return None
    if sec_fetch and sec_fetch not in {"same-origin", "none"}:
        return 403, "Cross-origin requests to the local server are blocked."
    if raw_origin := headers.get(b"origin", b"").decode("latin-1").strip():
        if not _origin_matches_local(raw_origin, raw_host, is_testclient):
            return 403, "Cross-origin requests to the local server are blocked."
    elif raw_referer := headers.get(b"referer", b"").decode("latin-1").strip():
        if not _origin_matches_local(raw_referer, raw_host, is_testclient):
            return 403, "Cross-origin Referer on local mutation blocked."
    if path.startswith(("/api/", "/v1/")):
        ctype = headers.get(b"content-type", b"").decode("latin-1").split(";", 1)[0].strip().lower()
        if ctype in {"text/plain", "application/x-www-form-urlencoded"}:
            return 415, "Unsupported Content-Type for API request."
        if ctype == "multipart/form-data" and not _is_multipart_allowed(path):
            return 415, "Unsupported Content-Type for API request."
    return None


def security_headers_for(path: str, *, local_mode: bool) -> tuple[tuple[bytes, bytes], ...]:
    """Return baseline security headers plus CSP/CORP/COOP; allow same-origin framing on local UI root only."""
    if not local_mode:
        return _BASE_HEADERS
    if path == "/":
        return _LOCAL_EMBED_BASE_HEADERS + _LOCAL_UI_EXTRA_HEADERS
    extra = ((b"cache-control", b"no-store"),) if path.startswith(("/api/", "/v1/")) else ()
    return _BASE_HEADERS + _LOCAL_EXTRA_HEADERS + extra


def install_safe_error_handlers(app: FastAPI) -> None:
    """Register 422 and 500 handlers that never echo raw secrets, inputs, or stack traces."""

    async def _validation_error(_req: Request, exc: RequestValidationError) -> JSONResponse:
        safe: list[dict[str, Any]] = [
            {"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")}
            for err in exc.errors()[:12]
        ]
        return JSONResponse(status_code=422, content={"detail": safe})

    async def _unhandled_error(_req: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    app.add_exception_handler(RequestValidationError, _validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_error)
