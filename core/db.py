"""Local JSON persistence for ingested knowledge chunks."""

import json
from pathlib import Path

from core.contracts import KnowledgeChunk


def save_chunks(chunks: list[KnowledgeChunk], db_path: Path) -> None:
    """Serialize chunks to a local JSON file."""
    payload = {"chunks": [chunk.model_dump() for chunk in chunks]}
    db_path.write_text(json.dumps(payload), encoding="utf-8")


def load_chunks(db_path: Path) -> list[KnowledgeChunk]:
    """Load and validate chunks from a JSON file, or return an empty list."""
    if not db_path.exists():
        return []
    payload = json.loads(db_path.read_text(encoding="utf-8"))
    return [KnowledgeChunk.model_validate(chunk) for chunk in payload.get("chunks", [])]