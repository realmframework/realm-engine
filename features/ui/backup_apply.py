"""Validate a complete restore plan before making reversible, non-destructive changes."""

from collections.abc import Callable
from contextlib import suppress
from pathlib import Path

from fastapi import HTTPException

from core.contracts import WorkspaceConfig
from core.db import atomic_write_bytes
from core.impact_contracts import FocusState, ImpactLedgerState
from core.linked_vaults import cache_index_for_dir, cache_study_path, is_linked_vault
from core.work_contracts import WorkBoardState
from core.workflow_contracts import WorkflowState
from features.ui import chat_store, folders, workspace
from features.ui.backup_archive import MAX_ARCHIVE_BYTES, bounded_bytes
from features.ui.backup_state import restored_state


def apply_restore(entries: dict[str, bytes], active: WorkspaceConfig, activate: Callable[[WorkspaceConfig], dict[str, object]]) -> dict[str, object]:
    if is_linked_vault(active.knowledge_dir, workspace.REPO_ROOT):
        raise HTTPException(status_code=403, detail="Linked folders are read-safe — restore backups into a managed workspace instead.")
    target = workspace.resolve_safe_knowledge_dir(active.knowledge_dir)
    chat_path = chat_store.area_chat_path(active.knowledge_dir)
    config, chats = restored_state(entries, active, target, chat_path)
    planned: list[tuple[Path, bytes]] = []
    wanted_folders = [folders.contained_path(target, name.rstrip("/")) for name in entries if name.endswith("/")]
    if any(folder.exists() and not folder.is_dir() for folder in wanted_folders):
        raise HTTPException(status_code=409, detail="A restored folder conflicts with an existing file. Choose a new workspace.")
    for name, raw in entries.items():
        if not name.lower().endswith(".md"):
            continue
        path = folders.contained_path(target, name)
        if path.exists():
            if not path.is_file() or bounded_bytes(path) != raw:
                raise HTTPException(status_code=409, detail="An existing guide differs. Restore into a new workspace to keep both versions.")
        else:
            planned.append((path, raw))
    extra_models = (("work_board.json", WorkBoardState), ("impact_ledger.json", ImpactLedgerState), ("focus_engine.json", FocusState), ("workflows.json", WorkflowState))
    extra_restores = [(cache_study_path(active.knowledge_dir, fname, workspace.REPO_ROOT), model.model_validate_json(entries[fname].decode("utf-8"))) for fname, model in extra_models if fname in entries]
    metadata = {workspace.WORKSPACE_FILE, chat_path, cache_index_for_dir(target, workspace.REPO_ROOT), *(p for p, _ in extra_restores)}
    original = {p: bounded_bytes(p, MAX_ARCHIVE_BYTES) if p.exists() else None for p in metadata}
    if any(p.is_symlink() for p in metadata) or chat_path.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Restore storage cannot be a symbolic link")
    created: list[Path] = []
    directories: list[Path] = []
    try:
        for path, raw in [(folder / "__folder_only__", b"") for folder in wanted_folders] + planned:
            missing: list[Path] = []
            parent = path.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for directory in reversed(missing):
                directory.mkdir()
                directories.append(directory)
            if path.name == "__folder_only__":
                continue
            with path.open("xb") as handle:
                created.append(path)
                handle.write(raw)
        chat_store.save_chats(chats, chat_path)
        for extra_path, extra_model in extra_restores:
            atomic_write_bytes(extra_path, extra_model.model_dump_json(indent=2).encode("utf-8"))
        payload = activate(config)
    except Exception:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        for directory in reversed(directories):
            with suppress(OSError):
                directory.rmdir()
        with suppress(Exception):
            activate(active)
        for path, raw in original.items():
            if raw is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write_bytes(path, raw)
        raise
    return {**payload, "restored_files": sum(name.lower().endswith(".md") for name in entries), "added_files": len(created), "restored_chats": len(chats)}
