"""Persistence and prompt-building helpers for built-in and user-defined output formats."""

import json
import re
from pathlib import Path

from core.format_presets import BUILTIN_FORMATS, OutputFormat

FORMATS_FILE = "output_formats.json"
_BUILTIN_IDS = {fmt.id for fmt in BUILTIN_FORMATS}


def _formats_path(root: Path) -> Path:
    return root.resolve() / FORMATS_FILE


def load_custom_formats(root: Path) -> list[OutputFormat]:
    path = _formats_path(root)
    if path.is_symlink() or not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(raw, list):
        return []
    out: list[OutputFormat] = []
    for item in raw:
        try:
            fmt = OutputFormat.model_validate({**item, "builtin": False})
            if fmt.id not in _BUILTIN_IDS:
                out.append(fmt)
        except (ValueError, TypeError):
            continue
    return out


def list_formats(root: Path) -> list[OutputFormat]:
    return [*BUILTIN_FORMATS, *load_custom_formats(root)]


def get_format(root: Path, format_id: str | None) -> OutputFormat | None:
    return next((f for f in list_formats(root) if f.id == format_id), None) if format_id else None


def save_custom_format(
    root: Path,
    name: str,
    sections: list[str],
    category: str = "Custom",
    description: str = "",
    instructions: str = "",
    format_id: str = "",
) -> OutputFormat:
    clean_name = name.strip()
    clean_sections = [s.strip() for s in sections if s and s.strip()][:16]
    if not clean_name or not clean_sections:
        raise ValueError("Provide a format name and at least one expected section.")
    slug = re.sub(r"[^a-z0-9]+", "_", (format_id or clean_name).strip().lower()).strip("_")[:48] or "custom_format"
    if slug in _BUILTIN_IDS:
        slug = f"custom_{slug}"
    item = OutputFormat(
        id=slug, name=clean_name, category=(category.strip() or "Custom")[:32],
        description=description.strip()[:220], sections=clean_sections,
        instructions=instructions.strip()[:1200], builtin=False,
    )
    existing = [f for f in load_custom_formats(root) if f.id != slug]
    existing.append(item)
    path = _formats_path(root)
    tmp = path.with_suffix(".json.tmp")
    if path.is_symlink() or tmp.is_symlink():
        raise ValueError("Output formats storage cannot be a symbolic link")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps([f.model_dump() for f in existing], indent=2), encoding="utf-8")
    tmp.replace(path)
    return item


def delete_custom_format(root: Path, format_id: str) -> bool:
    if format_id in _BUILTIN_IDS:
        raise ValueError("Built-in formats cannot be deleted.")
    existing = load_custom_formats(root)
    remaining = [f for f in existing if f.id != format_id]
    if len(remaining) == len(existing):
        return False
    path = _formats_path(root)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps([f.model_dump() for f in remaining], indent=2), encoding="utf-8")
    tmp.replace(path)
    return True


def build_format_instruction(fmt: OutputFormat, extra_note: str = "") -> str:
    outline = "\n".join(f"## {sec}" for sec in fmt.sections)
    extra = f"\nAdditional user focus: {extra_note.strip()}" if extra_note.strip() else ""
    rules = f"\nFormat guidelines: {fmt.instructions}" if fmt.instructions else ""
    return (
        f"Structure the output strictly as a polished '{fmt.name}' document in clean Markdown.\n"
        f"Use these exact top-level Markdown sections in order:\n{outline}{rules}{extra}\n"
        "Ground every point in the conversation, attached notes, and sources. "
        "If a required section lacks data, explicitly mark what is missing or TBD instead of inventing facts."
    )
