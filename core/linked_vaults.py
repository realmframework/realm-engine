"""Obsidian-style linked external folders (in-place vaults) and native OS folder picker."""

import json
import re
import subprocess
import sys
from pathlib import Path

from core.runtime import data_root

LINKED_FILE = "linked_vaults.json"
CACHE_DIR = ".vault_cache"
_RESERVED = {"knowledge_base", "core", "features", "src", "docs", "tests", "node_modules", "__pycache__", "build", "dist", "wheels"}


def _registry_path(root: Path) -> Path:
    return root.resolve() / LINKED_FILE


def load_linked_vaults(root: Path) -> dict[str, dict[str, str]]:
    """Return {slug: {'path': abs_path, 'label': display_name}} stored under ``root``."""
    reg = _registry_path(root)
    if reg.is_symlink() or not reg.is_file():
        return {}
    try:
        raw = json.loads(reg.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
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


def _save_linked_vaults(root: Path, data: dict[str, dict[str, str]]) -> None:
    reg, tmp = _registry_path(root), _registry_path(root).with_suffix(".json.tmp")
    if reg.is_symlink() or tmp.is_symlink():
        raise ValueError("Linked vault registry cannot be a symbolic link")
    reg.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(reg)


def resolve_linked_path(name: str, root: Path) -> Path | None:
    """Return the validated external directory for a linked vault slug, or None."""
    entry = load_linked_vaults(root).get(name)
    if not entry:
        return None
    target = Path(entry["path"]).expanduser()
    return target.resolve() if not target.is_symlink() and target.is_dir() else None


def is_linked_vault(name: str, root: Path) -> bool:
    return name in load_linked_vaults(root)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")[:56]
    return slug if slug and slug not in _RESERVED else f"vault_{slug or 'folder'}"


def link_folder(folder: Path, root: Path, label: str = "") -> tuple[str, Path]:
    """Register an existing folder on disk as an in-place REALM vault without copying files."""
    target = folder.expanduser()
    if target.is_symlink() or not target.is_dir():
        raise ValueError("Choose an existing folder (symbolic links are not allowed)")
    resolved, root_res = target.resolve(), root.resolve()
    if resolved == resolved.parent or resolved == root_res:
        raise ValueError("Cannot link the filesystem root or REALM internal storage directory")
    data = load_linked_vaults(root)
    for existing_slug, info in data.items():
        if Path(info["path"]).expanduser().resolve() == resolved:
            return existing_slug, resolved
    base_slug = _slugify(label or resolved.name)
    slug, suffix = base_slug, 2
    while slug in data or (root_res / slug).exists():
        slug, suffix = f"{base_slug[:58]}_{suffix}", suffix + 1
    data[slug] = {"path": str(resolved), "label": (label or resolved.name).strip() or slug}
    _save_linked_vaults(root, data)
    return slug, resolved


def unlink_folder(name: str, root: Path) -> bool:
    """Unlink a vault from REALM and remove only local cache files — NEVER deletes user files."""
    data = load_linked_vaults(root)
    if name not in data:
        return False
    data.pop(name, None)
    _save_linked_vaults(root, data)
    cache_root = root.resolve() / CACHE_DIR
    for suffix in (".index.json", ".chats.json"):
        item = cache_root / f"{name}{suffix}"
        if item.is_file() and not item.is_symlink():
            item.unlink(missing_ok=True)
    return True


def cache_index_for_dir(directory: Path, root: Path) -> Path:
    """Keep index.json inside managed vaults, or under .vault_cache for linked external folders."""
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


def pick_native_folder(prompt: str = "Choose a folder") -> Path | None:
    """Open the native macOS/Windows/Linux folder picker so directories are selectable."""
    safe = re.sub(r'["\\\r\n]', " ", prompt).strip() or "Choose a folder"
    if sys.platform == "darwin":
        proc = subprocess.run(["osascript", "-e", f'POSIX path of (choose folder with prompt "{safe}")'], capture_output=True, text=True, check=False)
        return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else None
    if sys.platform == "win32":
        ps = (
            "Add-Type -AssemblyName System.Windows.Forms;"
            "$d=New-Object System.Windows.Forms.FolderBrowserDialog;"
            f"$d.Description='{safe.replace(chr(39), '')}';$d.UseDescriptionForTitle=$true;"
            "if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){Write-Output $d.SelectedPath}"
        )
        proc = subprocess.run(["powershell", "-NoProfile", "-STA", "-Command", ps], capture_output=True, text=True, check=False)
        return Path(proc.stdout.strip()) if proc.returncode == 0 and proc.stdout.strip() else None
    for cmd in (["zenity", "--file-selection", "--directory", f"--title={safe}"], ["kdialog", "--getexistingdirectory", str(Path.home())]):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                return Path(proc.stdout.strip())
        except FileNotFoundError:
            continue
    return None
