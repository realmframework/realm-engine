"""Bounded knowledge-area discovery, ownership, deletion and graph metadata."""

import re
import shutil
import uuid
from collections.abc import Callable
from pathlib import Path

from core.contracts import KnowledgeArea, KnowledgeChunk
from core.db import load_chunks
from core.linked_vaults import (
    cache_index_for_dir,
    is_linked_vault,
    load_linked_vaults,
    resolve_linked_path,
    unlink_folder,
)
from features.ui.graph_data import area_graph

AREA_COLORS = ("#4BB8E8", "#38D399", "#F59E0B", "#A855F7", "#EC4899", "#3B82F6")
RESERVED_DIRS = {"core", "features", "src", "docs", "tests", "node_modules", "__pycache__", "build", "dist", "wheels"}
AREA_MARKER = ".knowledge-area.json"
DOCUMENT_EXTENSIONS = {".md", ".txt", ".html", ".pdf", ".docx", ".csv", ".tsv", ".xlsx", ".pptx"}


def validate_area_path(name: str, root: Path) -> Path:
    """Allow top-level vaults or explicitly linked external folders; reject symlinks."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", name) or name in RESERVED_DIRS:
        raise ValueError("Use a knowledge area name with lowercase letters, numbers, underscores or hyphens")
    linked = resolve_linked_path(name, root)
    if linked is not None:
        return linked
    candidate = root.resolve() / name
    if candidate.is_symlink() or candidate.resolve().parent != root.resolve():
        raise ValueError("Knowledge areas cannot be symbolic links or leave the workspace")
    if candidate.exists() and not candidate.is_dir():
        raise ValueError("Knowledge area must be a directory")
    return candidate


def area_path(name: str, root: Path, create: bool = False) -> Path:
    linked = resolve_linked_path(name, root)
    if linked is not None:
        return linked
    candidate = validate_area_path(name, root)
    if create:
        if not candidate.exists():
            candidate.mkdir()
        if candidate.is_dir() and name != "knowledge_base":
            if (candidate / AREA_MARKER).is_symlink():
                raise ValueError("Area marker cannot be a symbolic link")
            if not (candidate / AREA_MARKER).exists():
                (candidate / AREA_MARKER).write_text('{"version": 1, "id": "' + uuid.uuid4().hex + '"}\n', encoding="utf-8")
    if not candidate.is_dir():
        raise ValueError("Knowledge area does not exist")
    return candidate


def area_files(directory: Path) -> list[Path]:
    return [p for p in directory.rglob("*") if p.is_file() and not p.is_symlink() and not any(part.startswith(".") for part in p.relative_to(directory).parts) and p.resolve().is_relative_to(directory.resolve()) and p.suffix.lower() in DOCUMENT_EXTENSIONS]


def list_areas(root: Path, current: str = "knowledge_base") -> list[KnowledgeArea]:
    linked_map = load_linked_vaults(root)
    found: set[str] = {"knowledge_base", current, *linked_map.keys()}
    for child in root.iterdir():
        if child.is_dir() and not child.is_symlink() and re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", child.name) and child.name not in RESERVED_DIRS and ((child / AREA_MARKER).is_file() or (child / "index.json").is_file() or any(area_files(child))):
            found.add(child.name)
    result: list[KnowledgeArea] = []
    for index, name in enumerate(sorted(found, key=lambda n: (n != "knowledge_base", n))):
        try:
            directory = area_path(name, root)
        except ValueError:
            continue
        is_linked = name in linked_map
        count = len({p.with_suffix("") for p in area_files(directory)})
        cache = cache_index_for_dir(directory, root)
        if cache.is_file() and not cache.is_symlink():
            try:
                count = len({c.file_path for c in load_chunks(cache)})
            except (ValueError, OSError, TypeError, AttributeError):
                pass
        result.append(
            KnowledgeArea(
                name=name,
                doc_count=count,
                color=AREA_COLORS[index % len(AREA_COLORS)],
                can_delete=is_linked or (name != "knowledge_base" and (directory / AREA_MARKER).is_file()),
                linked=is_linked,
                linked_path=str(directory) if is_linked else "",
                display_name=linked_map[name]["label"] if is_linked else "",
            )
        )
    return result


def delete_area(name: str, root: Path) -> None:
    """Unlink external vaults safely without touching user files, or delete managed areas."""
    if name == "knowledge_base":
        raise ValueError("The default knowledge_base area cannot be deleted")
    if is_linked_vault(name, root):
        unlink_folder(name, root)
        return
    directory = area_path(name, root)
    marker = directory / AREA_MARKER
    if marker.is_symlink() or not marker.is_file():
        raise ValueError("Only managed custom knowledge areas can be deleted")
    shutil.rmtree(directory)


def _cached_area_chunks(directory: Path, ingest: Callable[[Path], list[KnowledgeChunk]], root: Path) -> list[KnowledgeChunk]:
    cache = cache_index_for_dir(directory, root)
    if cache.is_file() and not cache.is_symlink():
        files = area_files(directory)
        if files and max(p.stat().st_mtime_ns for p in files) < cache.stat().st_mtime_ns:
            try:
                cached = load_chunks(cache)
                if cached:
                    return cached
            except (ValueError, OSError, TypeError, AttributeError):
                pass
    return ingest(directory)


def graph_payload(areas: list[KnowledgeArea], root: Path, ingest: Callable[[Path], list[KnowledgeChunk]], url_template: str = "", excluded_map: dict[str, list[str]] | None = None) -> dict[str, object]:
    nodes: list[dict[str, object]] = []
    links: list[dict[str, str]] = []
    for area in areas:
        raw_chunks = _cached_area_chunks(area_path(area.name, root), ingest, root)
        excluded = (excluded_map or {}).get(area.name, [])
        chunks = [c for c in raw_chunks if not (c.subfolder and any(c.subfolder == ex or c.subfolder.startswith(ex + "/") for ex in excluded))] if excluded else raw_chunks
        area_nodes, area_links = area_graph(area, chunks, url_template=url_template)
        nodes.extend(area_nodes)
        links.extend(area_links)
    return {"nodes": nodes, "links": links, "areas": [a.model_dump() for a in areas]}


def area_identity(name: str, root: Path) -> str:
    """Distinguish a recreated custom vault from one deleted during a provider call."""
    if is_linked_vault(name, root):
        return f"linked:{area_path(name, root)}"
    return (area_path(name, root) / AREA_MARKER).read_text(encoding="utf-8") if name != "knowledge_base" else name
