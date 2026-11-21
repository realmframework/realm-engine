"""Bound transport bodies, audio uploads, and standard HTTP security headers."""

from collections.abc import Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.datastructures import UploadFile
from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_AUDIO_BYTES = 25 * 1024 * 1024
MAX_BATCH_BYTES = 64 * 1024 * 1024
SIZE_MESSAGE = "Each file must be 15 MB (15 MiB) or smaller. Upload a smaller file."
_GUARDED_PATHS = {"/api/upload", "/api/anonymize/preview", "/api/backup/import", "/api/audio/transcribe"}
_SECURITY_HEADERS = (
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"no-referrer"),
)


def check_file_size(raw: bytes) -> bytes:
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=SIZE_MESSAGE)
    return raw


async def read_file(file: UploadFile) -> bytes:
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=SIZE_MESSAGE)
    return check_file_size(await file.read(MAX_UPLOAD_BYTES + 1))


async def read_upload(request: Request, decode: Callable[..., tuple[list[tuple[str, bytes]], str | None]]) -> tuple[list[tuple[str, bytes]], str | None, object, object, object, list[str], bool]:
    if "application/json" in request.headers.get("content-type", ""):
        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Provide a JSON object")
        try:
            files, tags = decode(body)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="Invalid upload content") from exc
        for _, raw in files:
            check_file_size(raw)
        return files, tags, body.get("anonymize"), body.get("subfolder", ""), body.get("area"), [], False
    form = await request.form()
    try:
        uploads = [f for f in (*form.getlist("files"), *form.getlist("file")) if isinstance(f, UploadFile)]
        files = [(f.filename or "", await read_file(f)) for f in uploads]
        anonymize = str(form["anonymize"]).lower() not in ("false", "0", "no") if "anonymize" in form else None
        rel_paths = [str(v) for v in form.getlist("relative_paths")]
        skip_unsupported = str(form.get("skip_unsupported", "")).lower() in ("true", "1", "yes")
        return files, str(form["tags"]) if form.get("tags") else None, anonymize, str(form.get("subfolder", "")), form.get("area"), rel_paths, skip_unsupported
    finally:
        await form.close()


def _path_limit(path: str) -> tuple[int, str]:
    if path == "/api/backup/import":
        return MAX_BATCH_BYTES + 1024 * 1024, "Backup ZIP must be 64 MiB or smaller (65 MiB including request framing)."
    if path == "/api/audio/transcribe":
        return MAX_AUDIO_BYTES, "Audio upload must be 25 MiB or smaller."
    if path == "/api/upload":
        return MAX_BATCH_BYTES, SIZE_MESSAGE
    return MAX_UPLOAD_BYTES * 2, SIZE_MESSAGE


def upload_body_guard(app: ASGIApp) -> ASGIApp:
    async def bounded(scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = list(message.get("headers", []))
                present = {k.lower() for k, _ in existing}
                for key, val in _SECURITY_HEADERS:
                    if key not in present:
                        existing.append((key, val))
                message = {**message, "headers": existing}
            await send(message)

        path = str(scope.get("path", ""))
        if path not in _GUARDED_PATHS:
            await app(scope, receive, send_with_headers)
            return
        maximum, message_text = _path_limit(path)
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = 0
        if declared > maximum:
            await JSONResponse({"detail": message_text + " Combined request limit exceeded."}, status_code=413)(scope, receive, send_with_headers)
            return
        total = 0

        async def limited_receive() -> Message:
            nonlocal total
            message = await receive()
            total += len(message.get("body", b""))
            if total > maximum:
                raise HTTPException(status_code=413, detail=message_text + " Combined request is too large.")
            return message

        await app(scope, limited_receive, send_with_headers)

    return bounded
