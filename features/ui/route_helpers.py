"""Shared request-parsing and area-resolution helpers for UI FastAPI routers."""

from pathlib import Path

from fastapi import HTTPException, Request

from core.contracts import WorkspaceConfig


async def read_json_dict(
    request: Request,
    *,
    required: bool = True,
    non_dict_status: int = 400,
) -> dict[str, object]:
    """Parse a JSON object body safely, returning 400 on malformed JSON."""
    if not required and "application/json" not in request.headers.get("content-type", ""):
        return {}
    try:
        raw = await request.json()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Provide valid JSON") from exc
    if not isinstance(raw, dict):
        raise HTTPException(status_code=non_dict_status, detail="Provide a JSON object")
    return raw


def guide_area_slug(active: WorkspaceConfig, doc_id: str) -> str:
    """Resolve the owning knowledge-area slug for a single- or multi-area doc_id."""
    if len(active.active_dirs) > 1 and "::" in doc_id:
        return doc_id.split("::", 1)[0]
    return active.knowledge_dir


def safe_terminal_cwd(active: WorkspaceConfig, resolver: object, fallback: Path) -> Path:
    """Resolve the active workspace directory for new local terminal sessions."""
    if not active.knowledge_dir or not callable(resolver):
        return fallback
    try:
        res = resolver(active.knowledge_dir, create=False)
        return res if isinstance(res, Path) else fallback
    except (HTTPException, ValueError):
        return fallback
