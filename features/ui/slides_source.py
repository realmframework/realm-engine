"""Resolve chat turns, full chats, library guides, or raw Markdown for Slide Deck export."""

from collections.abc import Callable
from pathlib import Path

from fastapi import HTTPException, Request

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.runtime import bundle_root
from features.ui import chat_store, selection, workspace

_LOGO_EXTS = (".png", ".jpg", ".jpeg")


def _active_logo_path() -> Path | None:
    for ext in _LOGO_EXTS:
        cand = workspace.REPO_ROOT / f"custom_logo{ext}"
        if cand.is_file() and not cand.is_symlink():
            return cand
    default = bundle_root() / "features" / "ui" / "static" / "logo-512.png"
    return default if default.is_file() else None


def build_source_resolver(
    get_config: Callable[[], WorkspaceConfig],
    get_index: Callable[[], list[KnowledgeChunk]],
) -> Callable[[Request, dict[str, object]], tuple[str, str, str, list[str], Path | None, str, str]]:
    """Return a workspace-aware SourceResolver callback for features.slides.router."""

    def _resolve(request: Request, body: dict[str, object]) -> tuple[str, str, str, list[str], Path | None, str, str]:
        with workspace.STATE_LOCK:
            active = get_config()
            logo, accent, glow = _active_logo_path(), active.theme_accent, active.theme_glow
            chat_id = str(body.get("chat_id") or "").strip()
            doc_id = str(body.get("doc_id") or "").strip()

            if chat_id:
                free_chat, turn_index = bool(body.get("free_chat")), body.get("turn_index")
                if not free_chat:
                    workspace.require_area(request, active)
                    if not active.active_dirs:
                        raise HTTPException(status_code=404, detail="Chat session not found")
                area = chat_store.FREE_CHAT_AREA if free_chat else active.knowledge_dir
                session = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(area))
                if session is None or (not free_chat and not selection.chat_matches(session, active)):
                    raise HTTPException(status_code=404, detail="Chat session not found")
                if isinstance(turn_index, int) and 0 <= turn_index < len(session.turns):
                    t = session.turns[turn_index]
                    title = t.format_name or t.query[:80] or session.title
                    sub = f"{t.agent_name} · {t.created_at[:10]}" if t.agent_name else t.created_at[:10]
                    cites = list(t.tutor.cited_titles) if t.tutor else []
                    return title, (t.tutor.answer if t.tutor else t.query), sub, cites, logo, accent, glow
                parts = [
                    f"## {t.format_name or t.query[:75]}\n\n{t.tutor.answer if t.tutor else t.query}"
                    for t in session.turns
                ]
                cites = [c for t in session.turns if t.tutor for c in t.tutor.cited_titles]
                sub = f"{len(session.turns)} turns · {session.updated_at[:10]}"
                return session.title or "Conversation", "\n\n---\n\n".join(parts), sub, cites, logo, accent, glow

            if doc_id:
                workspace.require_area(request, active)
                matching = [c for c in get_index() if c.doc_id == doc_id]
                if not matching:
                    raise HTTPException(status_code=404, detail="Guide not found in active workspace")
                doc_title = matching[0].title.split(" — ")[0].strip() or doc_id
                sections = [
                    f"## {c.title.split(' — ', 1)[1].strip() if ' — ' in c.title else c.title}\n\n{c.content}"
                    for c in matching
                ]
                sub = f"{active.app_title} · {matching[0].subfolder or active.knowledge_dir}"
                return doc_title, "\n\n---\n\n".join(sections), sub, [doc_title], logo, accent, glow

            title = str(body.get("title") or "REALM Presentation").strip()
            md = str(body.get("markdown") or "").strip()
            sub = str(body.get("subtitle") or active.app_title).strip()
            raw_cites = body.get("citations")
            cites = [str(c) for c in raw_cites] if isinstance(raw_cites, list) else []
            return title, md, sub, cites, logo, accent, glow

    return _resolve
