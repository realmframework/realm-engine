"""Document ingestion service for the AI Engineering Knowledge Engine."""

import csv
from collections import Counter
from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from pypdf.errors import PdfReadError

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


def ingest_directory(dir_path: Path, *, read_only: bool = False) -> list[KnowledgeChunk]:
    """Recursively parse all supported files under ``dir_path``, skipping dot-folders & bad files."""
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
    md_stems = {p.relative_to(dir_path).with_suffix("").as_posix().casefold() for p in all_files if p.suffix.lower() == ".md"}
    non_md_counts = Counter(p.relative_to(dir_path).with_suffix("").as_posix().casefold() for p in all_files if p.suffix.lower() != ".md")
    chunks: list[KnowledgeChunk] = []
    for path in all_files:
        rel_stem = path.relative_to(dir_path).with_suffix("").as_posix()
        stem_key = rel_stem.casefold()
        if path.suffix.lower() != ".md" and stem_key in md_stems:
            continue
        stem_override = f"{rel_stem}__{path.suffix.lower().lstrip('.')}" if path.suffix.lower() != ".md" and non_md_counts[stem_key] > 1 else None
        try:
            chunks.extend(convert_file_to_chunks(path, knowledge_dir=dir_path, read_only=read_only, stem_override=stem_override))
        except (OSError, UnicodeError, ValueError, BadZipFile, ParseError, PdfReadError, csv.Error, EOFError, KeyError):
            continue
    return chunks
