"""Local JSON persistence and FastAPI routes for multi-turn chat sessions."""

import json
from datetime import UTC, datetime
from pathlib import Path

from core.contracts import ChatSession, ChatTurn
from core.runtime import data_root
from features.ui import workspace

REPO_ROOT = data_root()
CHATS_FILE = REPO_ROOT / "chats.json"


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).isoformat()


def load_chats(path: Path | None = None) -> list[ChatSession]:
    """Load persisted chat sessions from disk, returning an empty list when missing."""
    target = path or CHATS_FILE
    if not target.is_file():
        return []
    try:
        raw_items = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            return []
        return [ChatSession.model_validate(item) for item in raw_items]
    except (ValueError, OSError):
        return []


def save_chats(chats: list[ChatSession], path: Path | None = None) -> None:
    """Write the list of chat sessions to disk."""
    target = path or CHATS_FILE
    payload = [chat.model_dump() for chat in chats]
    temporary = target.with_suffix(".json.tmp")
    if target.is_symlink() or temporary.is_symlink():
        raise ValueError("Chat storage cannot be a symbolic link")
    temporary.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    temporary.replace(target)


def list_chat_summaries(path: Path | None = None) -> list[dict[str, object]]:
    """Return summary metadata for all saved chats sorted newest first."""
    chats = sorted(load_chats(path), key=lambda item: item.updated_at, reverse=True)
    return [
        {"chat_id": chat.chat_id, "title": chat.title, "updated_at": chat.updated_at, "turn_count": len(chat.turns), "area": chat.area, "active_dirs": chat.active_dirs or [chat.area]}
        for chat in chats
    ]


def get_chat_session(chat_id: str, path: Path | None = None) -> ChatSession | None:
    """Retrieve a single chat session by ID."""
    for chat in load_chats(path):
        if chat.chat_id == chat_id:
            return chat
    return None


def append_chat_turn(chat_id: str, turn: ChatTurn, path: Path | None = None, area: str = "knowledge_base", active_dirs: list[str] | None = None) -> ChatSession:
    """Append a turn to an existing or newly created chat session and persist it."""
    chats = load_chats(path)
    for idx, chat in enumerate(chats):
        if chat.chat_id == chat_id:
            updated_turns = [*chat.turns, turn]
            title = chat.title or turn.query[:60]
            updated_session = ChatSession(chat_id=chat_id, title=title, updated_at=turn.created_at, turns=updated_turns, area=area, active_dirs=active_dirs or [area], subfolder=turn.subfolder, doc_id=turn.doc_id)
            chats[idx] = updated_session
            save_chats(chats, path)
            return updated_session

    new_session = ChatSession(
        chat_id=chat_id,
        title=turn.query.strip()[:60] or "New Conversation",
        updated_at=turn.created_at,
        turns=[turn],
        area=area, active_dirs=active_dirs or [area], subfolder=turn.subfolder, doc_id=turn.doc_id,
    )
    chats.insert(0, new_session)
    save_chats(chats, path)
    return new_session


def delete_chat_session(chat_id: str, path: Path | None = None) -> bool:
    """Delete a chat session by ID and return whether a session was removed."""
    chats = load_chats(path)
    remaining = [chat for chat in chats if chat.chat_id != chat_id]
    if len(remaining) == len(chats):
        return False
    save_chats(remaining, path)
    return True


def area_chat_path(area: str) -> Path:
    """Keep legacy chats in the default area and custom vault chats in their own directory."""
    if area == "knowledge_base":
        return CHATS_FILE
    target = workspace.resolve_safe_knowledge_dir(area) / "chats.json"
    if target.is_symlink():
        raise ValueError("Area chat storage cannot be a symbolic link")
    return target
