"""Selected-area indexing, source identities and primary-compatible file destinations."""

from collections.abc import Callable
from pathlib import Path

from fastapi import HTTPException

from core.contracts import ChatSession, KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import cache_index_for_dir
from features.ui import areas, folders


def paths(config: WorkspaceConfig, root: Path, create: bool = False) -> list[Path]:
    candidates = [areas.validate_area_path(name, root) for name in config.active_dirs]
    if any(cache_index_for_dir(path, root).is_symlink() for path in candidates):
        raise ValueError("Area index cannot be a symbolic link")
    return [areas.area_path(name, root, create) for name in config.active_dirs]


def document_id(config: WorkspaceConfig, area: str, doc_id: str) -> str:
    return area + "::" + doc_id if len(config.active_dirs) > 1 else doc_id


def is_excluded(subfolder: str, excluded: list[str]) -> bool:
    return bool(subfolder) and any(subfolder == ex or subfolder.startswith(ex + "/") for ex in excluded)


def filter_chunks(chunks: list[KnowledgeChunk], area: str, config: WorkspaceConfig) -> list[KnowledgeChunk]:
    excluded = config.excluded_subfolders.get(area, [])
    return [c for c in chunks if not is_excluded(c.subfolder, excluded)] if excluded else chunks


def filter_subfolders(items: list[dict[str, object]], area: str, config: WorkspaceConfig) -> list[dict[str, object]]:
    excluded = config.excluded_subfolders.get(area, [])
    return [f for f in items if not is_excluded(str(f.get("path") or ""), excluded)] if excluded else items


def unloaded_subfolders(config: WorkspaceConfig) -> list[dict[str, str]]:
    multi = len(config.active_dirs) > 1
    out: list[dict[str, str]] = []
    for area in config.active_dirs:
        for rel in sorted(dict.fromkeys(config.excluded_subfolders.get(area, []))):
            if rel:
                out.append({"area": area, "path": rel, "full_path": f"{area}/{rel}" if multi else rel})
    return out


def merge(config: WorkspaceConfig, root: Path, load: Callable[[Path], list[KnowledgeChunk]]) -> list[KnowledgeChunk]:
    merged: list[KnowledgeChunk] = []
    for area, path in zip(config.active_dirs, paths(config, root, create=True), strict=True):
        chunks = filter_chunks(load(path), area, config)
        if len(config.active_dirs) > 1:
            chunks = [c.model_copy(update={"area": area, "id": area + "::" + c.id, "doc_id": document_id(config, area, c.doc_id),
                "subfolder": area + ("/" + c.subfolder if c.subfolder else ""), "title": area + " / " + c.title}) for c in chunks]
        merged.extend(chunks)
    return merged


def subfolders(config: WorkspaceConfig, root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for area, path in zip(config.active_dirs, paths(config, root), strict=True):
        for folder in filter_subfolders(folders.list_subfolders(path), area, config):
            relative = str(folder["path"])
            result.append({**folder, "area": area, "path": area + ("/" + relative if relative else "") if len(config.active_dirs) > 1 else relative})
    return result


def document_source(config: WorkspaceConfig, root: Path, doc_id: str) -> tuple[Path, str]:
    area, relative = config.knowledge_dir, doc_id
    if len(config.active_dirs) > 1:
        area, separator, relative = doc_id.partition("::")
        if not separator or area not in config.active_dirs:
            raise HTTPException(status_code=404, detail="Guide is outside the selected areas")
    return areas.area_path(area, root), relative


def folder_source(config: WorkspaceConfig, root: Path, path: str) -> tuple[Path, str]:
    area, relative = config.knowledge_dir, path
    if len(config.active_dirs) > 1 and path:
        area, _, relative = path.partition("/")
        if area not in config.active_dirs:
            raise HTTPException(status_code=400, detail="Choose a folder inside a selected area")
    return areas.area_path(area, root), relative


def chat_matches(chat: ChatSession, config: WorkspaceConfig) -> bool:
    return chat.area == config.knowledge_dir and (chat.active_dirs or [chat.area]) == config.active_dirs


def identities_unchanged(root: Path, identities: dict[str, str]) -> bool:
    try:
        return all(areas.area_path(name, root).is_dir() and not areas.area_path(name, root).is_symlink() and areas.area_identity(name, root) == identity for name, identity in identities.items())
    except (ValueError, OSError):
        return False
