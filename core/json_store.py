"""Shared atomic JSON persistence, per-path locking, IDs, ISO-date validation, and area header checks."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import Path
from threading import Lock, RLock

from fastapi import HTTPException, Request
from pydantic import BaseModel

from core.contracts import WorkspaceConfig
from core.db import atomic_write_text, backup_corrupt_file
from core.linked_vaults import CACHE_DIR, cache_study_path
from core.runtime import data_root

_LOCKS_GUARD = Lock()
_PATH_LOCKS: dict[str, RLock] = {}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def today_iso() -> str:
    return date.today().isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def validate_iso_date(value: str, *, allow_empty: bool = True, field_name: str = "date") -> str:
    """Validate that a string is a real YYYY-MM-DD calendar date (or empty when allowed)."""
    cleaned = (value or "").strip()
    if not cleaned:
        if allow_empty:
            return ""
        raise ValueError(f"{field_name} is required (YYYY-MM-DD)")
    try:
        date.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(f"Invalid calendar {field_name}: '{cleaned}'") from exc
    return cleaned


def store_lock(path: Path) -> RLock:
    """Return a shared re-entrant lock keyed by canonical store file path."""
    key = str(path.resolve())
    with _LOCKS_GUARD:
        lock = _PATH_LOCKS.get(key)
        if lock is None:
            lock = RLock()
            _PATH_LOCKS[key] = lock
        return lock


def area_store_path(area: str, filename: str, root: Path | None = None) -> Path:
    """Resolve and symlink-check a workspace-scoped JSON sidecar storage path."""
    resolved_root = (root or data_root()).resolve()
    if not area or not area.strip():
        cache = resolved_root / CACHE_DIR
        cache.mkdir(parents=True, exist_ok=True)
        target = cache / f"_default.{filename}"
    else:
        target = cache_study_path(area.strip(), filename, resolved_root)
    if target.is_symlink() or target.with_suffix(".json.tmp").is_symlink():
        raise ValueError(f"Storage path '{filename}' cannot be a symbolic link")
    return target


def load_model_json[TModel: BaseModel](path: Path, model_cls: type[TModel], default_factory: Callable[[], TModel]) -> TModel:
    """Load and validate a Pydantic model from JSON, backing up corrupt files cleanly."""
    if path.is_symlink():
        raise ValueError("Storage path cannot be a symbolic link")
    if not path.is_file():
        return default_factory()
    try:
        return model_cls.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError:
        backup_corrupt_file(path)
        return default_factory()
    except OSError:
        return default_factory()


def save_model_json[TModel: BaseModel](state: TModel, path: Path, model_cls: type[TModel]) -> TModel:
    """Re-validate candidate state (enforcing list caps and field bounds) before atomic write."""
    if path.is_symlink() or path.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Storage path cannot be a symbolic link")
    validated = model_cls.model_validate(state.model_dump())
    atomic_write_text(path, validated.model_dump_json(indent=2))
    return validated


def require_area_header(request: Request, config: WorkspaceConfig) -> None:
    """Guard mutations against cross-workspace races when X-Knowledge-Area header is supplied."""
    hdr = (request.headers.get("x-knowledge-area") or "").strip()
    if hdr and hdr != config.knowledge_dir:
        raise HTTPException(
            status_code=409,
            detail=f"Active workspace changed from '{hdr}' to '{config.knowledge_dir}'. Reload and retry.",
        )
