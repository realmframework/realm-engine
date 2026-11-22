"""Resumable SHA-256 verified downloader & zip-slip safe archive extractor for Built-in AI."""

from __future__ import annotations

import os
import shutil
import stat
import tarfile
import time
import zipfile
from collections.abc import Callable
from pathlib import Path
from threading import Event
from urllib.parse import urljoin

import httpx

from core.local_ai_catalog import is_allowed_download_url
from core.local_ai_paths import safe_member_path, sha256_file
from core.net_security import resolve_pinned_url

ProgressFn = Callable[[str, int, float, float], None]
_CHUNK_BYTES, _MAX_REDIRECTS = 262_144, 6


def _validate_download_url(url: str) -> str:
    if not is_allowed_download_url(url):
        raise ValueError("Download URL is not on an approved official release host.")
    clean, _, _, _ = resolve_pinned_url(url, allowed_ports=frozenset({443}), resolve_dns=False)
    return clean


def download_verified_file(
    url: str, dest: Path, expected_sha256: str, expected_size: int, stage: str,
    *, on_progress: ProgressFn | None = None, cancel_event: Event | None = None, client: httpx.Client | None = None,
) -> Path:
    """Download with HTTPS allowlist, Range resume, cancellation & mandatory SHA-256 check."""
    if dest.is_symlink() or dest.parent.is_symlink():
        raise ValueError("Download destination cannot be a symbolic link.")
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.parent / f"{dest.name}.part"
    if part.is_symlink():
        raise ValueError("Partial download file cannot be a symbolic link.")
    existing = part.stat().st_size if part.is_file() else 0
    if existing > expected_size > 0:
        part.unlink(missing_ok=True)
        existing = 0
    own_client = client is None
    http = client or httpx.Client(follow_redirects=False, timeout=httpx.Timeout(60.0, connect=15.0))
    try:
        current = _validate_download_url(url)
        headers = {"Range": f"bytes={existing}-"} if existing > 0 else {}
        for _ in range(_MAX_REDIRECTS + 1):
            with http.stream("GET", current, headers=headers) as resp:
                if resp.status_code in {301, 302, 303, 307, 308}:
                    loc = resp.headers.get("location", "")
                    if not loc:
                        raise ValueError("Empty redirect while downloading local AI asset.")
                    current = _validate_download_url(urljoin(current, loc))
                    continue
                if resp.status_code == 416 and existing > 0:
                    break
                if resp.status_code not in {200, 206}:
                    raise ValueError(f"Download server returned HTTP {resp.status_code}.")
                append = resp.status_code == 206 and existing > 0
                downloaded = existing if append else 0
                total = expected_size or (downloaded + int(resp.headers.get("content-length") or 0))
                last_emit, last_pct = 0.0, -1
                with part.open("ab" if append else "wb") as out:
                    for chunk in resp.iter_bytes(_CHUNK_BYTES):
                        if cancel_event is not None and cancel_event.is_set():
                            raise InterruptedError("Download cancelled.")
                        out.write(chunk)
                        downloaded += len(chunk)
                        pct = min(100, int(downloaded * 100 / max(1, total)))
                        now = time.monotonic()
                        if on_progress and (pct != last_pct and (now - last_emit >= 0.2 or pct == 100)):
                            on_progress(stage, pct, round(downloaded / 1048576, 1), round(total / 1048576, 1))
                            last_emit, last_pct = now, pct
                break
        else:
            raise ValueError("Too many redirects while downloading local AI asset.")
    finally:
        if own_client:
            http.close()
    if on_progress:
        on_progress(f"verify_{stage}", 100, round(expected_size / 1048576, 1), round(expected_size / 1048576, 1))
    if expected_sha256 and sha256_file(part, _CHUNK_BYTES) != expected_sha256.lower():
        part.unlink(missing_ok=True)
        raise ValueError("Integrity verification failed; downloaded file was discarded for safety.")
    os.replace(part, dest)
    return dest


def safe_extract_archive(archive_path: Path, target_dir: Path, binary_name: str) -> Path:
    """Safely unpack tar.gz or zip runtime archive, rejecting zip-slip and outside symlinks."""
    staging = target_dir.parent / f".extract_{target_dir.name}"
    shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True, exist_ok=True)
    root = staging.resolve()
    try:
        if archive_path.name.endswith(".zip"):
            with zipfile.ZipFile(archive_path) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        safe_member_path(root, info.filename).mkdir(parents=True, exist_ok=True)
                        continue
                    if stat.S_ISLNK(info.external_attr >> 16):
                        raise ValueError("Symlink entries are not permitted in zip archives.")
                    out = safe_member_path(root, info.filename)
                    out.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info, "r") as src, out.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
        else:
            with tarfile.open(archive_path, "r:*") as tf:
                for mem in tf.getmembers():
                    if mem.isdev() or mem.islnk():
                        raise ValueError(f"Unsupported archive entry: {mem.name}")
                    out = safe_member_path(root, mem.name)
                    if mem.isdir():
                        out.mkdir(parents=True, exist_ok=True)
                    elif mem.issym():
                        link_target = (out.parent / mem.linkname).resolve()
                        if link_target != root and root not in link_target.parents:
                            raise ValueError(f"Unsafe symlink in archive: {mem.name}")
                        out.parent.mkdir(parents=True, exist_ok=True)
                        if not out.exists() and not out.is_symlink():
                            os.symlink(mem.linkname, out)
                    elif mem.isfile() and (src := tf.extractfile(mem)) is not None:
                        out.parent.mkdir(parents=True, exist_ok=True)
                        with src, out.open("wb") as dst:
                            shutil.copyfileobj(src, dst)
                        out.chmod(0o755 if (mem.mode & 0o111) or out.name == binary_name else 0o644)
        if target_dir.exists():
            shutil.rmtree(target_dir)
        os.replace(staging, target_dir)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    found = next((p for p in (target_dir / binary_name, *sorted(target_dir.rglob(binary_name))) if p.is_file() and not p.is_symlink()), None)
    if found is None:
        raise ValueError(f"Archive did not contain {binary_name}.")
    found.chmod(0o755)
    return found
