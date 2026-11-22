"""Paths, machine-local state persistence, installed inventory & disk space for Built-in AI."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from core.json_store import load_model_json, save_model_json
from core.local_ai_catalog import (
    LLAMA_RELEASE_TAG,
    MODEL_BY_ID,
    MODEL_PRESETS,
    RUNTIME_ASSETS,
    detect_platform_key,
)
from core.local_ai_contracts import LocalAiState
from core.runtime import data_root

_STATE_FILE = "local_ai_state.json"


def runtime_root(root: Path | None = None) -> Path:
    return (root or data_root()) / "runtime" / "local_ai"


def bin_dir(root: Path | None = None, tag: str = LLAMA_RELEASE_TAG) -> Path:
    return runtime_root(root) / "bin" / tag


def models_dir(root: Path | None = None) -> Path:
    return runtime_root(root) / "models"


def model_file_path(model_id: str, root: Path | None = None) -> Path:
    return models_dir(root) / MODEL_BY_ID[model_id].filename


def find_llama_binary(binary_name: str, root: Path | None = None, tag: str = LLAMA_RELEASE_TAG) -> Path | None:
    base = bin_dir(root, tag)
    if not base.is_dir() or base.is_symlink():
        return None
    for cand in (base / binary_name, *sorted(base.rglob(binary_name))):
        if cand.is_file() and not cand.is_symlink():
            return cand
    return None


def load_local_ai_state(root: Path | None = None) -> LocalAiState:
    return load_model_json((root or data_root()) / _STATE_FILE, LocalAiState, LocalAiState)


def save_local_ai_state(state: LocalAiState, root: Path | None = None) -> LocalAiState:
    return save_model_json(state, (root or data_root()) / _STATE_FILE, LocalAiState)


def list_installed_builtin_models(root: Path | None = None) -> list[str]:
    mdir = models_dir(root)
    if not mdir.is_dir():
        return []
    return [p.id for p in MODEL_PRESETS if (mdir / p.filename).is_file() and not (mdir / p.filename).is_symlink()]


def runtime_binary_path(root: Path | None = None) -> Path | None:
    pkey = detect_platform_key()
    if pkey is None:
        return None
    asset = RUNTIME_ASSETS[pkey]
    state = load_local_ai_state(root)
    tag = state.installed_runtime_tag or LLAMA_RELEASE_TAG
    return find_llama_binary(asset.binary_name, root, tag) or find_llama_binary(asset.binary_name, root, LLAMA_RELEASE_TAG)


def disk_usage_summary(root: Path | None = None) -> tuple[int, float]:
    base = root or data_root()
    base.mkdir(parents=True, exist_ok=True)
    rt = runtime_root(base)
    used = sum(p.stat().st_size for p in rt.rglob("*") if p.is_file() and not p.is_symlink()) if rt.is_dir() else 0
    free_bytes = shutil.disk_usage(base).free
    return round(used / (1024 * 1024)), round(free_bytes / (1024**3), 2)


def check_disk_space(needed_bytes: int, root: Path | None = None) -> None:
    base = root or data_root()
    base.mkdir(parents=True, exist_ok=True)
    required = int(needed_bytes * 1.15) + 256 * 1024 * 1024
    free = shutil.disk_usage(base).free
    if free < required:
        raise ValueError(f"Not enough free disk space: need ~{required / 1024**3:.1f} GB, only {free / 1024**3:.1f} GB available.")


def remove_local_ai_files(root: Path | None = None) -> int:
    """Delete downloaded runtime and models under data_root; returns freed MiB."""
    base = root or data_root()
    used_mb, _ = disk_usage_summary(base)
    rt = runtime_root(base)
    if rt.exists() and not rt.is_symlink():
        shutil.rmtree(rt)
    save_local_ai_state(LocalAiState(), base)
    return used_mb


def sha256_file(path: Path, chunk_bytes: int = 262_144) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(chunk_bytes):
            h.update(chunk)
    return h.hexdigest().lower()


def safe_member_path(target_root: Path, rel: str) -> Path:
    norm = Path(rel)
    if norm.is_absolute() or ".." in norm.parts:
        raise ValueError(f"Unsafe archive entry path: {rel}")
    resolved = (target_root / norm).resolve()
    if resolved != target_root and target_root not in resolved.parents:
        raise ValueError(f"Archive path escapes target directory: {rel}")
    return resolved
