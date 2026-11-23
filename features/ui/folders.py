"""Physical subfolder discovery and safe document paths within one knowledge area."""

import os
import re
from pathlib import Path, PurePosixPath

from core.file_types import ALL_EXTENSIONS, CODE_EXTENSIONS, is_ignored_relpath

EXTENSIONS = ALL_EXTENSIONS
_WIN_RESERVED = frozenset({"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))})


def _is_reparse(path: Path) -> bool:
    is_junction = getattr(os.path, "isjunction", None)
    return path.is_symlink() or (callable(is_junction) and bool(is_junction(path)))


def _is_unsafe_segment(part: str) -> bool:
    if part in {"", ".", ".."} or part.startswith(".") or part.endswith((".", " ")):
        return True
    return part.split(".", 1)[0].upper() in _WIN_RESERVED


def contained_path(base: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or re.search(r"[\\\x00-\x1f]", relative):
        raise ValueError("Use a relative path inside this knowledge area")
    parts = relative.split("/")
    if any(_is_unsafe_segment(part) for part in parts):
        raise ValueError("Hidden, reserved, trailing-dot/space, and parent paths are not allowed")
    candidate = base
    for part in parts:
        candidate = candidate / part
        if _is_reparse(candidate):
            raise ValueError("Symbolic links cannot be used as subfolders or guides")
    if not candidate.resolve().is_relative_to(base.resolve()):
        raise ValueError("Path must stay inside the knowledge area")
    return candidate


def resolve_subfolder(base: Path, subfolder: object, create: bool = False) -> Path:
    if not isinstance(subfolder, str):
        raise TypeError("Subfolder must be a relative path")
    if subfolder == "":
        return base
    if any(not re.fullmatch(r"[\w][\w .-]{0,63}", part) or _is_unsafe_segment(part) for part in subfolder.split("/")):
        raise ValueError("Use valid folder names with letters, numbers, spaces, underscores or hyphens")
    target = contained_path(base, subfolder)
    if create:
        target.mkdir(parents=True, exist_ok=True)
    if not target.is_dir():
        raise ValueError("Subfolder does not exist")
    return target


def resolve_document(base: Path, doc_id: str) -> Path:
    probe = contained_path(base, doc_id)
    parent = probe.parent
    if parent.is_dir():
        stem_lower, want_ext = probe.name.lower(), ""
        if "__" in stem_lower:
            cand_stem, cand_ext = stem_lower.rsplit("__", 1)
            if cand_stem and f".{cand_ext}" in EXTENSIONS:
                stem_lower, want_ext = cand_stem, f".{cand_ext}"
        by_ext: dict[str, Path] = {}
        for entry in sorted(parent.iterdir()):
            if entry.stem.lower() != stem_lower or entry.suffix.lower() not in EXTENSIONS:
                continue
            if _is_reparse(entry):
                raise ValueError("Symbolic links cannot be used as subfolders or guides")
            if entry.is_file() and entry.resolve().is_relative_to(base.resolve()):
                by_ext.setdefault(entry.suffix.lower(), entry)
        if want_ext and want_ext in by_ext:
            return by_ext[want_ext]
        for extension in EXTENSIONS:
            if extension in by_ext:
                return by_ext[extension]
    raise ValueError("Guide not found")


def list_subfolders(base: Path) -> list[dict[str, object]]:
    folders: dict[str, int] = {"": 0}
    documents: set[str] = set()
    for path in base.rglob("*"):
        rel_obj = path.relative_to(base)
        if is_ignored_relpath(rel_obj):
            continue
        relative = rel_obj.as_posix()
        try:
            contained_path(base, relative)
        except ValueError:
            continue
        if path.is_dir():
            folders.setdefault(relative, 0)
        elif path.is_file() and path.suffix.lower() in EXTENSIONS:
            documents.add(rel_obj.as_posix() if path.suffix.lower() in CODE_EXTENSIONS else rel_obj.with_suffix("").as_posix())
    for document in documents:
        parent = PurePosixPath(document).parent
        folders[parent.as_posix() if parent != PurePosixPath(".") else ""] += 1
    return [{"path": path, "doc_count": count} for path, count in sorted(folders.items())]
