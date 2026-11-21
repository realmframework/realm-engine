"""Document ingestion service for the AI Engineering Knowledge Engine."""

from pathlib import Path

from core.contracts import KnowledgeChunk
from features.ingestion.anonymizer import anonymize_text
from features.ingestion.converters import (
    SUPPORTED_EXTENSIONS,
    convert_bytes_to_markdown,
    convert_file_to_chunks,
)
from features.ingestion.embedder import (
    DEFAULT_EMBED_MODEL,
    DEFAULT_OLLAMA_EMBED_URL,
    embed_chunk,
    embed_text,
    hydrate_embeddings,
)
from features.ingestion.parser import parse_markdown_file

__all__ = [
    "DEFAULT_EMBED_MODEL",
    "DEFAULT_OLLAMA_EMBED_URL",
    "SUPPORTED_EXTENSIONS",
    "anonymize_text",
    "convert_bytes_to_markdown",
    "convert_file_to_chunks",
    "embed_chunk",
    "embed_text",
    "hydrate_embeddings",
    "ingest_directory",
    "parse_markdown_file",
]


def ingest_directory(dir_path: Path) -> list[KnowledgeChunk]:
    """Recursively parse all supported files under ``dir_path``, skipping dot-folders (.obsidian, .git)."""
    resolved_root = dir_path.resolve()
    all_files = sorted(
        path
        for path in dir_path.rglob("*")
        if path.is_file()
        and not path.is_symlink()
        and not any(part.startswith(".") for part in path.relative_to(dir_path).parts)
        and path.resolve().is_relative_to(resolved_root)
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    md_stems = {p.with_suffix("") for p in all_files if p.suffix.lower() == ".md"}
    chunks: list[KnowledgeChunk] = []
    for path in all_files:
        if path.suffix.lower() != ".md" and path.with_suffix("") in md_stems:
            continue
        chunks.extend(convert_file_to_chunks(path, knowledge_dir=dir_path))
    return chunks
