"""Bounded ZIP encoding and validation; never use extract/extractall on user archives."""

import io
import stat
import struct
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import HTTPException

MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_MEMBERS = 2048


def member_path(name: str) -> PurePosixPath:
    parts = name.rstrip("/").split("/")
    if not name or any(p in {"", ".", ".."} or p.startswith(".") for p in parts) or any(c in name for c in "\\:\x00") or any(ord(c) < 32 for c in name):
        raise ValueError("Backup contains an unsafe path")
    path = PurePosixPath(*parts)
    if path.is_absolute():
        raise ValueError("Backup paths must be relative")
    return path


def bounded_bytes(path: Path, limit: int = MAX_FILE_BYTES) -> bytes:
    if path.is_symlink():
        raise ValueError("Backup files cannot be symbolic links")
    with path.open("rb") as handle:
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise HTTPException(status_code=413, detail="Backup is too large. Use a smaller workspace (15 MiB per file, 64 MiB total).")
    return raw


def preflight_archive(raw: bytes) -> None:
    """Bound central-directory work before ZipFile allocates a record for every member."""
    end = raw.rfind(b"PK\x05\x06", max(0, len(raw) - 65557))
    if end < 0 or end + 22 > len(raw):
        raise ValueError("Missing ZIP directory")
    disk, start_disk, on_disk, count, size, offset, comment = struct.unpack_from("<4H2IH", raw, end + 4)
    if disk or start_disk or on_disk != count or end + 22 + comment != len(raw) or offset + size != end:
        raise ValueError("Use a standard, single-part ZIP backup")
    if count > MAX_MEMBERS:
        raise HTTPException(status_code=413, detail="Backup contains too many items (maximum 2,048).")
    position, actual = offset, 0
    while position < end:
        if actual >= MAX_MEMBERS:
            raise HTTPException(status_code=413, detail="Backup contains too many items (maximum 2,048).")
        if position + 46 > end or raw[position:position + 4] != b"PK\x01\x02":
            raise ValueError("Invalid ZIP directory")
        name, extra, note = struct.unpack_from("<3H", raw, position + 28)
        position += 46 + name + extra + note
        actual += 1
    if position != end or actual != count:
        raise ValueError("Invalid ZIP directory size")


def read_archive(raw: bytes) -> dict[str, bytes]:
    if len(raw) > MAX_ARCHIVE_BYTES:
        raise HTTPException(status_code=413, detail="Backup ZIP must be 64 MiB or smaller.")
    preflight_archive(raw)
    entries: dict[str, bytes] = {}
    seen: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if len(archive.infolist()) > MAX_MEMBERS:
            raise HTTPException(status_code=413, detail="Backup contains too many items (maximum 2,048).")
        total = 0
        for info in archive.infolist():
            path = member_path(info.orig_filename)
            key = unicodedata.normalize("NFC", str(path)).casefold()
            if key in seen or stat.S_IFMT(info.external_attr >> 16) not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Backup contains duplicate paths or special files")
            seen.add(key)
            total += info.file_size
            if info.file_size > MAX_FILE_BYTES or total > MAX_ARCHIVE_BYTES:
                raise HTTPException(status_code=413, detail="Expanded backup exceeds the 15 MiB/file or 64 MiB total limit.")
            if info.flag_bits & 1 or info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                raise ValueError("Use an unencrypted, standard ZIP backup")
            if info.is_dir():
                entries[str(path) + "/"] = b""
                continue
            if path.suffix.lower() == ".md" or str(path) in {"workspace.json", "chats.json", "work_board.json", "impact_ledger.json", "focus_engine.json"}:
                with archive.open(info) as handle:
                    content = handle.read(MAX_FILE_BYTES + 1)
                if len(content) != info.file_size or len(content) > MAX_FILE_BYTES:
                    raise ValueError("Backup member size is invalid")
                content.decode("utf-8")
                entries[str(path)] = content
    if not entries:
        raise ValueError("No Markdown guides, settings or chats found in this backup")
    return entries


def make_archive(entries: dict[str, bytes]) -> bytes:
    if len(entries) > MAX_MEMBERS or any(len(raw) > MAX_FILE_BYTES for raw in entries.values()) or sum(map(len, entries.values())) > MAX_ARCHIVE_BYTES:
        raise HTTPException(status_code=413, detail="Workspace is too large for one backup (15 MiB/file, 64 MiB total, 2,048 items).")
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in entries.items():
            member_path(name)
            archive.writestr(name, raw)
    if output.tell() > MAX_ARCHIVE_BYTES:
        raise HTTPException(status_code=413, detail="Compressed backup exceeds 64 MiB.")
    return output.getvalue()
