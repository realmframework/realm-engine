"""Validate portable settings and chat history without importing keys or loosening policy."""

import json
from pathlib import Path

from fastapi import HTTPException

from core.contracts import ChatSession, WorkspaceConfig
from features.ui.backup_archive import bounded_bytes, member_path


def parse_chats(raw: bytes) -> list[ChatSession]:
    items = json.loads(raw)
    if not isinstance(items, list):
        raise TypeError("Backup chats must be a list")
    chats = [ChatSession.model_validate(item) for item in items]
    if len({chat.chat_id for chat in chats}) != len(chats):
        raise ValueError("Duplicate conversation IDs")
    return chats


def current_chats(path: Path) -> list[ChatSession]:
    if path.is_symlink():
        raise ValueError("Chat storage cannot be a symbolic link")
    return parse_chats(bounded_bytes(path)) if path.exists() else []


def portable_chat(chat: ChatSession, target: Path, area: str) -> ChatSession:
    for scope in [chat, *chat.turns]:
        if scope.doc_id is not None:
            member_path(scope.doc_id + ".md")
        if scope.subfolder:
            member_path(scope.subfolder + "/guide.md")
    turns = []
    for turn in chat.turns:
        results = []
        for result in turn.results:
            doc_id = result.chunk.doc_id or Path(result.chunk.file_path).stem
            relative = member_path(doc_id + ".md")
            chunk = result.chunk.model_copy(update={"doc_id": doc_id, "file_path": str(target / str(relative))})
            results.append(result.model_copy(update={"chunk": chunk}))
        turns.append(turn.model_copy(update={"results": results}))
    return chat.model_copy(update={"area": area, "active_dirs": [area] if chat.active_dirs else [], "turns": turns})


def restored_state(entries: dict[str, bytes], active: WorkspaceConfig, target: Path, chat_path: Path) -> tuple[WorkspaceConfig, list[ChatSession]]:
    incoming = WorkspaceConfig.model_validate_json(entries["workspace.json"]) if "workspace.json" in entries else active
    strict = active.strict_local_only or incoming.strict_local_only
    config = incoming.model_copy(update={"knowledge_dir": active.knowledge_dir, "active_dirs": list(active.active_dirs), "strict_local_only": strict, "anonymize_uploads": active.anonymize_uploads or incoming.anonymize_uploads,
        "daily_cloud_request_limit": min(active.daily_cloud_request_limit, incoming.daily_cloud_request_limit),
        "daily_budget_usd_limit": min(active.daily_budget_usd_limit, incoming.daily_budget_usd_limit),
        "run_mode": "local" if strict and incoming.run_mode == "cloud" else incoming.run_mode})
    chats = {chat.chat_id: chat for chat in current_chats(chat_path)}
    for raw_chat in parse_chats(entries.get("chats.json", b"[]")):
        chat = portable_chat(raw_chat, target, active.knowledge_dir)
        if chat.chat_id in chats and chats[chat.chat_id] != chat:
            raise HTTPException(status_code=409, detail="A saved chat differs. Restore into a new workspace to keep both versions.")
        chats[chat.chat_id] = chat
    return config, list(chats.values())
