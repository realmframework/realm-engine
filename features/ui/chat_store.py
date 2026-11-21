"""Local JSON persistence and helpers for multi-turn vault and Free Chat sessions."""

import json
from datetime import UTC, datetime
from pathlib import Path

from core.contracts import ChatSession, ChatTurn
from core.db import atomic_write_text, backup_corrupt_file
from core.linked_vaults import is_linked_vault, linked_chats_path
from core.runtime import data_root
from features.ui import workspace

REPO_ROOT = data_root()
CHATS_FILE = REPO_ROOT / "chats.json"
FREE_CHAT_AREA = "__free__"


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def _parse_chat_list(target: Path, *, strict_io: bool) -> list[ChatSession]:
    if target.is_symlink():
        raise ValueError("Chat storage cannot be a symbolic link")
    if not target.is_file():
        return []
    try:
        raw_text = target.read_text(encoding="utf-8")
    except OSError:
        if strict_io:
            raise
        return []
    try:
        raw_items = json.loads(raw_text)
    except ValueError:
        if strict_io:
            backup_corrupt_file(target)
        return []
    if not isinstance(raw_items, list):
        if strict_io:
            backup_corrupt_file(target)
        return []
    sessions: list[ChatSession] = []
    had_corrupt = False
    for item in raw_items:
        try:
            sessions.append(ChatSession.model_validate(item))
        except (ValueError, TypeError):
            had_corrupt = True
    if had_corrupt and strict_io:
        backup_corrupt_file(target)
    return sessions


def load_chats(path: Path | None = None) -> list[ChatSession]:
    try:
        return _parse_chat_list(path or CHATS_FILE, strict_io=False)
    except ValueError:
        return []
def _strip_chat_embeddings(raw: dict[str, object]) -> dict[str, object]:
    turns = raw.get("turns")
    if isinstance(turns, list):
        for turn in turns:
            if isinstance(turn, dict) and isinstance((results := turn.get("results")), list):
                for res in results:
                    if isinstance(res, dict) and isinstance((chunk := res.get("chunk")), dict):
                        chunk["embedding"] = None
    return raw
def save_chats(chats: list[ChatSession], path: Path | None = None) -> None:
    """Atomically write chat sessions to disk without raw embedding vector bloat."""
    target = path or CHATS_FILE
    if target.is_symlink() or target.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Chat storage cannot be a symbolic link")
    payload = [_strip_chat_embeddings(chat.model_dump()) for chat in chats]
    atomic_write_text(target, json.dumps(payload, indent=2))


def list_chat_summaries(path: Path | None = None) -> list[dict[str, object]]:
    """Return summary metadata for all saved chats sorted newest first."""
    chats = sorted(load_chats(path), key=lambda item: item.updated_at, reverse=True)
    return [
        {"chat_id": c.chat_id, "title": c.title, "updated_at": c.updated_at, "turn_count": len(c.turns), "area": c.area, "active_dirs": c.active_dirs or [c.area], "free_chat": c.free_chat or c.area == FREE_CHAT_AREA, "last_agent_id": c.last_agent_id}
        for c in chats
    ]


def get_chat_session(chat_id: str, path: Path | None = None) -> ChatSession | None:
    """Retrieve a single chat session by ID."""
    return next((chat for chat in load_chats(path) if chat.chat_id == chat_id), None)


def save_chat_session(session: ChatSession, path: Path | None = None) -> ChatSession:
    """Insert or replace one ChatSession cleanly on disk without wiping on I/O errors."""
    target = path or CHATS_FILE
    chats = _parse_chat_list(target, strict_io=True)
    for idx, item in enumerate(chats):
        if item.chat_id == session.chat_id:
            chats[idx] = session
            save_chats(chats, target)
            return session
    chats.insert(0, session)
    save_chats(chats, target)
    return session


def append_chat_turn(chat_id: str, turn: ChatTurn, path: Path | None = None, area: str = "knowledge_base", active_dirs: list[str] | None = None) -> ChatSession:
    """Append a turn to an existing or newly created chat session and persist it."""
    target = path or CHATS_FILE
    chats, is_free = _parse_chat_list(target, strict_io=True), area == FREE_CHAT_AREA
    dirs = [FREE_CHAT_AREA] if is_free else (active_dirs or [area])
    for idx, chat in enumerate(chats):
        if chat.chat_id == chat_id:
            title = chat.title if chat.title and chat.title != "New Conversation" else (turn.query.strip()[:60] or "New Conversation")
            updated = chat.model_copy(update={"title": title, "updated_at": turn.created_at, "turns": [*chat.turns, turn], "area": area, "active_dirs": dirs, "subfolder": turn.subfolder, "doc_id": turn.doc_id, "free_chat": is_free, "last_agent_id": turn.agent_id or chat.last_agent_id})
            chats[idx] = updated
            save_chats(chats, target)
            return updated

    new_session = ChatSession(chat_id=chat_id, title=turn.query.strip()[:60] or "New Conversation", updated_at=turn.created_at, turns=[turn], area=area, active_dirs=dirs, subfolder=turn.subfolder, doc_id=turn.doc_id, free_chat=is_free, last_agent_id=turn.agent_id)
    chats.insert(0, new_session)
    save_chats(chats, target)
    return new_session


def delete_chat_session(chat_id: str, path: Path | None = None) -> bool:
    """Delete a chat session by ID and return whether a session was removed."""
    target = path or CHATS_FILE
    chats = _parse_chat_list(target, strict_io=True)
    remaining = [chat for chat in chats if chat.chat_id != chat_id]
    if len(remaining) == len(chats):
        return False
    save_chats(remaining, target)
    return True


def area_chat_path(area: str) -> Path:
    """Keep default chats in root, free/linked chats in .vault_cache, custom chats in dir."""
    if area == FREE_CHAT_AREA or is_linked_vault(area, workspace.REPO_ROOT):
        target = linked_chats_path(area, workspace.REPO_ROOT)
    elif area == "knowledge_base":
        target = CHATS_FILE
    else:
        target = workspace.resolve_safe_knowledge_dir(area) / "chats.json"
    if target.is_symlink():
        raise ValueError("Area chat storage cannot be a symbolic link")
    return target
