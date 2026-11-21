"""Atomic, fsync-durable local JSON/binary persistence and self-healing chunk cache."""

import json
import os
import shutil
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from core.contracts import KnowledgeChunk
from core.logging_config import get_logger

CHUNK_SCHEMA_VERSION = 1
_LOG = get_logger("db")


def atomic_write_bytes(path: Path, data: bytes, *, mode: int | None = None) -> None:
    """Write ``data`` to ``path`` via a unique sibling temp file with fsync, rejecting symlinks."""
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError(f"Storage path cannot be a symbolic link: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            tmp_path = Path(handle.name)
            if mode is not None and os.name != "nt":
                os.chmod(tmp_path, mode)
            handle.write(data)
            handle.flush()
            with suppress(OSError):
                os.fsync(handle.fileno())
        if mode is not None and os.name != "nt":
            os.chmod(tmp_path, mode)
        tmp_path.replace(path)
    except Exception:
        if tmp_path is not None:
            with suppress(OSError):
                tmp_path.unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, content: str, *, mode: int | None = None) -> None:
    """Atomically write UTF-8 text to ``path`` with fsync durability."""
    atomic_write_bytes(path, content.encode("utf-8"), mode=mode)


def backup_corrupt_file(path: Path, *, mode: int | None = None) -> Path | None:
    """Preserve a corrupted store alongside a .corrupt copy (timestamped if one already exists)."""
    if not path.is_file() or path.is_symlink():
        return None
    primary = path.with_suffix(path.suffix + ".corrupt")
    if not primary.exists() and not primary.is_symlink():
        backup = primary
    else:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup = path.with_name(f"{path.name}.corrupt.{stamp}")
        if backup.exists():
            backup = path.with_name(f"{path.name}.corrupt.{stamp}.{os.getpid()}")
    if backup.is_symlink():
        return None
    with suppress(OSError):
        shutil.copy2(path, backup)
        if mode is not None and os.name != "nt":
            os.chmod(backup, mode)
        _LOG.warning("Backed up corrupted store %s to %s", path.name, backup.name)
        return backup
    return None


def save_chunks(
    chunks: list[KnowledgeChunk],
    db_path: Path,
    *,
    embedding_model: str = "",
    embedding_provider: str = "",
) -> None:
    """Atomically serialize chunks and embedding metadata to a local JSON file."""
    first_dim = next((len(c.embedding) for c in chunks if c.embedding), 0)
    payload: dict[str, object] = {
        "schema_version": CHUNK_SCHEMA_VERSION,
        "embedding_provider": embedding_provider,
        "embedding_model": embedding_model,
        "embedding_dim": first_dim,
        "chunks": [chunk.model_dump() for chunk in chunks],
    }
    atomic_write_text(db_path, json.dumps(payload))


def load_chunks_meta(db_path: Path) -> tuple[list[KnowledgeChunk], dict[str, object]]:
    """Load chunks plus cache metadata, backing up corrupt cache files cleanly."""
    if not db_path.is_file() or db_path.is_symlink():
        return [], {}
    try:
        payload = json.loads(db_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("chunks"), list):
            backup_corrupt_file(db_path)
            return [], {}
        meta: dict[str, object] = {
            "schema_version": int(payload.get("schema_version") or 1),
            "embedding_provider": str(payload.get("embedding_provider") or ""),
            "embedding_model": str(payload.get("embedding_model") or ""),
            "embedding_dim": int(payload.get("embedding_dim") or 0),
        }
        return [KnowledgeChunk.model_validate(chunk) for chunk in payload["chunks"]], meta
    except (ValueError, TypeError):
        backup_corrupt_file(db_path)
        return [], {}
    except OSError:
        return [], {}


def load_chunks(db_path: Path) -> list[KnowledgeChunk]:
    """Load and validate chunks from a JSON file, self-healing to [] on corrupt cache."""
    return load_chunks_meta(db_path)[0]
