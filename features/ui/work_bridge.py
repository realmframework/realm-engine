"""Workspace bridge callbacks for Work Board extraction and RAG Library snapshot sync."""

from collections.abc import Callable
from pathlib import Path

from fastapi import HTTPException

from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.db import atomic_write_text
from core.linked_vaults import is_linked_vault
from features.ui import chat_store, selection, workspace


def build_work_source_resolver(
    get_config: Callable[[], WorkspaceConfig],
    get_index: Callable[[], list[KnowledgeChunk]],
) -> Callable[[str, int | None, str, str], str]:
    """Resolve chat turn, full chat, Library document, or raw text into Markdown for task extraction."""

    def _resolve(chat_id: str, turn_index: int | None, doc_id: str, text: str) -> str:
        if text.strip():
            return text.strip()
        with workspace.STATE_LOCK:
            active = get_config()
            if chat_id:
                session = None
                for area in (active.knowledge_dir, chat_store.FREE_CHAT_AREA):
                    if not area:
                        continue
                    try:
                        cand = chat_store.get_chat_session(chat_id, chat_store.area_chat_path(area))
                    except (ValueError, HTTPException):
                        cand = None
                    if cand is not None and (area == chat_store.FREE_CHAT_AREA or selection.chat_matches(cand, active)):
                        session = cand
                        break
                if session is None:
                    raise HTTPException(status_code=404, detail="Chat session not found")
                if turn_index is not None and 0 <= turn_index < len(session.turns):
                    turn = session.turns[turn_index]
                    return turn.tutor.answer if turn.tutor else turn.query
                return "\n\n".join(t.tutor.answer if t.tutor else t.query for t in session.turns)
            if doc_id:
                chunks = [c for c in get_index() if c.doc_id == doc_id]
                if not chunks:
                    raise HTTPException(status_code=404, detail="Guide not found in active workspace")
                return "\n\n".join(c.content for c in chunks)
        return ""

    return _resolve


def build_work_vault_sync(
    get_config: Callable[[], WorkspaceConfig],
    reindex: Callable[[Path], list[KnowledgeChunk]],
) -> Callable[[str, str, str], dict[str, object]]:
    """Save the Work Board Markdown snapshot into a managed workspace and refresh RAG index."""

    def _sync(area: str, filename: str, markdown: str) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = get_config()
            if not area or area != active.knowledge_dir:
                raise HTTPException(status_code=409, detail="Workspace changed. Retry sync.")
            if is_linked_vault(area, workspace.REPO_ROOT):
                raise HTTPException(status_code=403, detail="Linked folders are read-safe; switch to a managed workspace to save a Library snapshot.")
            target = workspace.resolve_safe_knowledge_dir(area, create=True)
            out_file = target / Path(filename).name
            if out_file.is_symlink():
                raise HTTPException(status_code=400, detail="Snapshot file cannot be a symbolic link")
            atomic_write_text(out_file, markdown)
            chunks = reindex(target)
            return {"ok": True, "doc_id": out_file.stem, "filename": out_file.name, "doc_count": len(workspace.group_chunks_into_guides(chunks))}

    return _sync
