"""Selected-area indexing, source identities and primary-compatible file destinations."""

from collections.abc import Callable
from pathlib import Path

from fastapi import HTTPException

from core.contracts import ChatSession, KnowledgeChunk, WorkspaceConfig
from features.ui import areas, folders


def paths(config: WorkspaceConfig, root: Path, create: bool = False) -> list[Path]:
    candidates = [areas.validate_area_path(name, root) for name in config.active_dirs]
    if any((path / "index.json").is_symlink() for path in candidates):
        raise ValueError("Area index cannot be a symbolic link")
    return [areas.area_path(name, root, create) for name in config.active_dirs]


def document_id(config: WorkspaceConfig, area: str, doc_id: str) -> str:
    return area + "::" + doc_id if len(config.active_dirs) > 1 else doc_id


def merge(config: WorkspaceConfig, root: Path, load: Callable[[Path], list[KnowledgeChunk]]) -> list[KnowledgeChunk]:
    merged: list[KnowledgeChunk] = []
    for area, path in zip(config.active_dirs, paths(config, root, create=True), strict=True):
        chunks = load(path)
        if len(config.active_dirs) > 1:
            chunks = [c.model_copy(update={"area": area, "id": area + "::" + c.id, "doc_id": document_id(config, area, c.doc_id),
                "subfolder": area + ("/" + c.subfolder if c.subfolder else ""), "title": area + " / " + c.title}) for c in chunks]
        merged.extend(chunks)
    return merged


def subfolders(config: WorkspaceConfig, root: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for area, path in zip(config.active_dirs, paths(config, root), strict=True):
        for folder in folders.list_subfolders(path):
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
        return all((root / name).is_dir() and not (root / name).is_symlink() and areas.area_identity(name, root) == identity for name, identity in identities.items())
    except (ValueError, OSError):
        return False
