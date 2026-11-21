"""Physical subfolder discovery and safe document paths within one knowledge area."""

import re
from pathlib import Path, PurePosixPath

EXTENSIONS = (".md", ".txt", ".html", ".docx", ".pdf", ".csv", ".tsv", ".xlsx", ".pptx")


def contained_path(base: Path, relative: str) -> Path:
    if not relative or relative.startswith("/") or re.search(r"[\\\x00-\x1f]", relative):
        raise ValueError("Use a relative path inside this knowledge area")
    parts = relative.split("/")
    if any(part in {"", ".", ".."} or part.startswith(".") for part in parts):
        raise ValueError("Hidden folders and parent paths are not allowed")
    candidate = base
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("Symbolic links cannot be used as subfolders or guides")
    if not candidate.resolve().is_relative_to(base.resolve()):
        raise ValueError("Path must stay inside the knowledge area")
    return candidate


def resolve_subfolder(base: Path, subfolder: object, create: bool = False) -> Path:
    if not isinstance(subfolder, str):
        raise TypeError("Subfolder must be a relative path")
    if subfolder == "":
        return base
    if any(not re.fullmatch(r"[\w][\w .-]{0,63}", part) for part in subfolder.split("/")):
        raise ValueError("Use folder names with letters, numbers, spaces, underscores or hyphens")
    target = contained_path(base, subfolder)
    if create:
        target.mkdir(parents=True, exist_ok=True)
    if not target.is_dir():
        raise ValueError("Subfolder does not exist")
    return target


def resolve_document(base: Path, doc_id: str) -> Path:
    for extension in EXTENSIONS:
        path = contained_path(base, doc_id + extension)
        if path.is_file():
            return path
    raise ValueError("Guide not found")


def list_subfolders(base: Path) -> list[dict[str, object]]:
    folders: dict[str, int] = {"": 0}
    documents: set[str] = set()
    for path in base.rglob("*"):
        relative = path.relative_to(base).as_posix()
        try:
            contained_path(base, relative)
        except ValueError:
            continue
        if path.is_dir():
            folders.setdefault(relative, 0)
        elif path.is_file() and path.suffix.lower() in EXTENSIONS:
            documents.add(path.relative_to(base).with_suffix("").as_posix())
    for document in documents:
        parent = PurePosixPath(document).parent
        folders[parent.as_posix() if parent != PurePosixPath(".") else ""] += 1
    return [{"path": path, "doc_count": count} for path, count in sorted(folders.items())]
