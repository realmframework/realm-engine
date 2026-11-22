"""Obsidian-style linked external folders (in-place vaults) and non-polluting caches."""

import json
import os
import re
from pathlib import Path

from core.db import atomic_write_text, backup_corrupt_file
from core.native_picker import pick_native_folder
from core.runtime import data_root

__all__ = [
    "CACHE_DIR", "LINKED_FILE", "cache_index_for_dir", "cache_study_path",
    "is_linked_vault", "link_folder", "linked_chats_path", "load_linked_vaults",
    "pick_native_folder", "resolve_linked_path", "unlink_folder", "validate_external_folder",
]

LINKED_FILE, CACHE_DIR = "linked_vaults.json", ".vault_cache"
_RESERVED = {"agents", "core", "features", "src", "docs", "tests", "node_modules", "__pycache__", "build", "dist", "wheels"}
_MAC_OS_ALIASES = frozenset({"/var", "/tmp", "/etc"})
_SYSTEM_ROOTS = frozenset({"/etc", "/private/etc", "/system", "/usr", "/bin", "/sbin", "/proc", "/sys", "/dev", "c:/windows", "c:/program files", "c:/program files (x86)", "c:/programdata"})
def _registry_path(root: Path) -> Path:
    return root.resolve() / LINKED_FILE

def _has_unsafe_symlink(target: Path) -> bool:
    is_junc = getattr(os.path, "isjunction", lambda _p: False)
    for anc in (target, *target.parents):
        if anc == anc.parent:
            break
        if str(anc) in _MAC_OS_ALIASES and anc != target:
            continue
        if anc.is_symlink() or is_junc(anc):
            return True
    return False

def _read_linked_vaults(root: Path, *, strict_io: bool) -> dict[str, dict[str, str]]:
    reg = _registry_path(root)
    if reg.is_symlink():
        if strict_io:
            raise ValueError("Linked vault registry cannot be a symbolic link")
        return {}
    if not reg.is_file():
        return {}
    try:
        raw = json.loads(reg.read_text(encoding="utf-8"))
    except OSError:
        if strict_io:
            raise
        return {}
    except ValueError:
        if strict_io:
            backup_corrupt_file(reg)
        return {}
    if not isinstance(raw, dict):
        if strict_io:
            backup_corrupt_file(reg)
        return {}
    out: dict[str, dict[str, str]] = {}
    for slug, info in raw.items():
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", slug) or slug in _RESERVED:
            continue
        if isinstance(info, str):
            out[slug] = {"path": info, "label": Path(info).name or slug}
        elif isinstance(info, dict) and isinstance(info.get("path"), str):
            out[slug] = {"path": info["path"], "label": str(info.get("label") or Path(info["path"]).name or slug)}
    return out
def load_linked_vaults(root: Path) -> dict[str, dict[str, str]]:
    return _read_linked_vaults(root, strict_io=False)
def _save_linked_vaults(root: Path, data: dict[str, dict[str, str]]) -> None:
    reg = _registry_path(root)
    if reg.is_symlink() or reg.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Linked vault registry cannot be a symbolic link")
    atomic_write_text(reg, json.dumps(data, indent=2))
def resolve_linked_path(name: str, root: Path) -> Path | None:
    entry = load_linked_vaults(root).get(name)
    target = Path(entry["path"]).expanduser() if entry else None
    return target.resolve() if target is not None and not _has_unsafe_symlink(target) and target.is_dir() else None
def is_linked_vault(name: str, root: Path) -> bool:
    return name in load_linked_vaults(root)

def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")[:56]
    return slug if slug and slug not in _RESERVED else f"vault_{slug or 'folder'}"


def validate_external_folder(folder: Path, root: Path, *, action: str = "link", allow_under_root: bool = False) -> Path:
    """Validate that an external directory is real, non-symlinked, non-system, non-hidden, and safe."""
    target = folder.expanduser()
    if _has_unsafe_symlink(target) or not target.is_dir():
        raise ValueError("Choose an existing folder (symbolic links are not allowed)")
    resolved, root_res = target.resolve(), root.resolve()
    if resolved == resolved.parent or root_res.is_relative_to(resolved) or (not allow_under_root and resolved.is_relative_to(root_res)):
        raise ValueError(f"Cannot {action} the filesystem root or REALM internal storage directory")
    if allow_under_root and resolved.is_relative_to(root_res) and resolved.relative_to(root_res).parts[:1] in {("agents",), (CACHE_DIR,)}:
        raise ValueError(f"Cannot {action} REALM internal storage directories")
    low = resolved.as_posix().lower()
    if low in _SYSTEM_ROOTS or any(low.startswith(r + "/") for r in _SYSTEM_ROOTS) or any(p.startswith(".") for p in resolved.parts if p not in {".", ".."}):
        raise ValueError(f"Cannot {action} system or hidden directories")
    return resolved


def link_folder(folder: Path, root: Path, label: str = "") -> tuple[str, Path]:
    """Register an existing folder on disk as an in-place REALM vault without copying files."""
    resolved, root_res = validate_external_folder(folder, root, action="link"), root.resolve()
    data = _read_linked_vaults(root, strict_io=True)
    for existing_slug, info in data.items():
        if Path(info["path"]).expanduser().resolve() == resolved:
            return existing_slug, resolved
    base_slug, suffix = _slugify(label or resolved.name), 2
    slug = base_slug
    while slug in data or (root_res / slug).exists():
        slug, suffix = f"{base_slug[:58]}_{suffix}", suffix + 1
    data[slug] = {"path": str(resolved), "label": (label or resolved.name).strip() or slug}
    _save_linked_vaults(root, data)
    return slug, resolved
def unlink_folder(name: str, root: Path) -> bool:
    data = _read_linked_vaults(root, strict_io=True)
    if name not in data:
        return False
    data.pop(name, None)
    _save_linked_vaults(root, data)
    cache_root = root.resolve() / CACHE_DIR
    for suffix in (".index.json", ".chats.json", ".study_deck.json", ".study_progress.json", ".work_board.json", ".impact_ledger.json", ".focus_engine.json", ".workflows.json"):
        item = cache_root / f"{name}{suffix}"
        if item.is_file() and not item.is_symlink():
            item.unlink(missing_ok=True)
    return True
def cache_index_for_dir(directory: Path, root: Path) -> Path:
    resolved, root_res = directory.resolve(), root.resolve()
    if resolved.parent == root_res:
        return directory / "index.json"
    for slug, info in load_linked_vaults(root).items():
        if Path(info["path"]).expanduser().resolve() == resolved:
            cache_dir = root_res / CACHE_DIR
            cache_dir.mkdir(parents=True, exist_ok=True)
            return cache_dir / f"{slug}.index.json"
    return directory / "index.json"
def linked_chats_path(name: str, root: Path | None = None) -> Path:
    base = (root or data_root()).resolve() / CACHE_DIR
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{name}.chats.json"
def cache_study_path(area_name: str, filename: str, root: Path | None = None) -> Path:
    """Store study decks/progress in .vault_cache for linked vaults so external folders stay clean."""
    resolved_root = (root or data_root()).resolve()
    if is_linked_vault(area_name, resolved_root):
        cache_dir = resolved_root / CACHE_DIR
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir / f"{area_name}.{filename}"
    return (resolved_root / area_name) / filename
