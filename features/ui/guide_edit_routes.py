"""In-app Markdown guide reading, editing, and structured creation routes."""

import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.db import atomic_write_text
from core.file_types import EDITABLE_TEXT_EXTENSIONS, code_language_for
from core.linked_vaults import is_linked_vault
from features.ui import folders, route_helpers, selection, upload_guard, workspace

MAX_MARKDOWN_BYTES = min(upload_guard.MAX_UPLOAD_BYTES, 1_000_000)
_EDITABLE_SUFFIXES = EDITABLE_TEXT_EXTENSIONS

def _safe_slug(title: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", title.strip()).strip("_").lower()[:64] or "note"

def _unique_md_path(destination: Path, stem: str) -> Path:
    candidate = destination / f"{stem}.md"
    if not candidate.exists() and not candidate.is_symlink():
        return candidate
    for idx in range(2, 500):
        numbered = destination / f"{stem}-{idx}.md"
        if not numbered.exists() and not numbered.is_symlink():
            return numbered
    raise ValueError("Too many guides share this title in the destination folder")


def _format_new_guide_markdown(title: str, content: str, tags: list[str], citations: list[str]) -> str:
    body = content.strip()
    if body.startswith("---\n"):
        return body + "\n"
    safe_title = title.strip().replace("\n", " ").replace('"', "'") or "Untitled Note"
    clean_tags = list(dict.fromkeys(t for tag in tags if (t := re.sub(r"[^a-z0-9_-]+", "-", tag.strip().lower()).strip("-"))))
    lines = ["---", f'title: "{safe_title}"', f"created_at: {datetime.now(UTC).strftime('%Y-%m-%d')}"]
    if clean_tags:
        lines.append("tags: [" + ", ".join(clean_tags) + "]")
    lines.extend(["---", ""])
    if not body.lstrip().startswith("# "):
        lines.extend([f"# {safe_title}", ""])
    lines.append(body)
    clean_cites = [c.strip() for c in citations if c.strip()]
    if clean_cites and "## Sources" not in body:
        lines.extend(["", "## Sources", *[f"- {cite}" for cite in dict.fromkeys(clean_cites)]])
    return "\n".join(lines).rstrip() + "\n"


def build_router(config: Callable[[], WorkspaceConfig], reindex: Callable[[Path], list[KnowledgeChunk]]) -> APIRouter:
    router = APIRouter()

    @router.get("/api/guides/{doc_id:path}/raw")
    def read_raw_guide(doc_id: str, request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.active_dirs:
                raise HTTPException(status_code=400, detail="Create or link a workspace first.")
            target, local_id = workspace.resolve_selected_guide(active, doc_id)
            selection.assert_guide_not_excluded(active, route_helpers.guide_area_slug(active, doc_id), local_id)
            path = workspace.resolve_guide_file(target, local_id)
            if path.is_symlink():
                raise HTTPException(status_code=400, detail="Symbolic links cannot be edited")
            if path.suffix.lower() not in _EDITABLE_SUFFIXES:
                raise HTTPException(status_code=400, detail="Only text, Markdown, and source-code files can be opened in the code/text editor.")
            if path.stat().st_size > MAX_MARKDOWN_BYTES:
                raise HTTPException(status_code=413, detail="Guide is too large to edit in-app")
            rel = path.relative_to(target)
            return {"doc_id": doc_id, "filename": path.name, "language": code_language_for(path.name), "subfolder": "" if rel.parent == Path(".") else rel.parent.as_posix(), "raw_markdown": path.read_text(encoding="utf-8", errors="replace")}

    @router.put("/api/guides/{doc_id:path}/raw")
    async def save_raw_guide(doc_id: str, request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        if not isinstance(body.get("content"), str):
            raise HTTPException(status_code=422, detail="Provide Markdown content as a string")
        raw_text = str(body["content"])
        if len(raw_text.encode("utf-8")) > MAX_MARKDOWN_BYTES:
            raise HTTPException(status_code=413, detail="Guide content exceeds the 1 MB editor limit")
        if not raw_text.strip():
            raise HTTPException(status_code=400, detail="Guide content cannot be empty")

        def _save() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace first.")
                area_slug = route_helpers.guide_area_slug(active, doc_id)
                if is_linked_vault(area_slug, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — edit files directly in your folder or copy them into a managed workspace.")
                target, local_id = workspace.resolve_selected_guide(active, doc_id)
                selection.assert_guide_not_excluded(active, area_slug, local_id)
                path = workspace.resolve_guide_file(target, local_id)
                if path.is_symlink():
                    raise HTTPException(status_code=400, detail="Symbolic links cannot be edited")
                if path.suffix.lower() not in _EDITABLE_SUFFIXES:
                    raise HTTPException(status_code=400, detail="Only Markdown, text, and source-code files can be edited in-app.")
                atomic_write_text(path, raw_text.rstrip() + "\n")
                chunks = reindex(target)
                return {**workspace.build_workspace_payload(active, chunks), "doc_id": doc_id, "guide": next((g for g in workspace.group_chunks_into_guides(chunks) if g["doc_id"] == doc_id), None)}

        return await run_in_threadpool(_save)

    @router.post("/api/guides/create")
    async def create_guide(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        title, content = str(body.get("title") or "").strip()[:160], str(body.get("content") or "")
        if not title or not content.strip():
            raise HTTPException(status_code=400, detail="Provide both a title and Markdown content")
        if len(content.encode("utf-8")) > MAX_MARKDOWN_BYTES:
            raise HTTPException(status_code=413, detail="Guide content exceeds the 1 MB limit")
        raw_tags, raw_cites = body.get("tags"), body.get("citations")
        tags = [str(t) for t in raw_tags] if isinstance(raw_tags, list) else [t.strip() for t in str(raw_tags or "").split(",") if t.strip()]
        citations, subfolder, req_area = ([str(c) for c in raw_cites] if isinstance(raw_cites, list) else []), str(body.get("subfolder") or "").strip(), str(body.get("area") or "").strip()

        def _create() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace before saving guides.")
                area = req_area or active.knowledge_dir
                if area not in active.active_dirs:
                    raise HTTPException(status_code=400, detail="Save to one of the active workspaces")
                if is_linked_vault(area, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — create guides in a managed workspace instead.")
                target = workspace.resolve_safe_knowledge_dir(area, create=False)
                try:
                    out_path = _unique_md_path(folders.resolve_subfolder(target, subfolder, create=True), _safe_slug(title))
                except ValueError as exc:
                    raise HTTPException(status_code=400, detail=str(exc)) from exc
                except (TypeError, OSError) as exc:
                    raise HTTPException(status_code=400, detail="Could not create guide in the selected folder") from exc
                atomic_write_text(out_path, _format_new_guide_markdown(title, content, tags, citations))
                chunks = reindex(target)
                rel_id = out_path.relative_to(target).with_suffix("").as_posix()
                full_id = f"{area}::{rel_id}" if len(active.active_dirs) > 1 else rel_id
                return {**workspace.build_workspace_payload(active, chunks), "doc_id": full_id, "title": title, "area": area, "subfolder": subfolder, "guide": next((g for g in workspace.group_chunks_into_guides(chunks) if g["doc_id"] == full_id), None)}

        return await run_in_threadpool(_create)

    return router
