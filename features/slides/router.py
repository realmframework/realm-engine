"""FastAPI router for native .pptx and 16:9 PDF slide deck export."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from features.slides.service import export_deck_bytes

_SLUG_RE = re.compile(r"[^a-z0-9]+")

SourceResolver = Callable[[Request, dict[str, object]], tuple[str, str, str, list[str], Path | None, str, str]]


def build_router(resolve_source: SourceResolver) -> APIRouter:
    router = APIRouter()

    @router.post("/api/export/slides")
    async def export_slides(request: Request) -> Response:
        try:
            body = await request.json()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Provide valid JSON") from exc
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="Provide a JSON object")

        raw_fmt = str(body.get("format") or "pptx").strip().lower()
        fmt: Literal["pptx", "pdf"] = "pdf" if raw_fmt == "pdf" else "pptx"

        def _build() -> tuple[str, bytes, str, str]:
            title, md, subtitle, citations, logo, accent, glow = resolve_source(request, body)
            if not md.strip():
                raise HTTPException(status_code=400, detail="Provide content to convert into slides")
            data, mime, ext, _ = export_deck_bytes(
                title,
                md,
                subtitle=subtitle,
                citations=citations,
                accent_hex=accent,
                glow_hex=glow,
                logo_path=logo,
                fmt=fmt,
            )
            return title, data, mime, ext

        title, data, mime, ext = await run_in_threadpool(_build)
        slug = _SLUG_RE.sub("-", title.lower()).strip("-")[:60] or "realm-slides"
        filename = f"{slug}-slides{ext}"
        return Response(
            data,
            media_type=mime,
            headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
        )

    return router
