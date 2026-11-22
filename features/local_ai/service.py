"""Service logic for Built-in Private AI setup, status, configuration & uninstall."""

from __future__ import annotations

import queue
import threading
from collections.abc import Iterator
from pathlib import Path

import httpx
from fastapi import HTTPException

from core import local_ai_catalog as _cat
from core import local_ai_installer as _inst
from core import local_ai_paths as _paths
from core.hardware import physical_ram_gb
from core.local_ai_contracts import (
    LocalAiConfigUpdate,
    LocalAiPresetView,
    LocalAiRunState,
    LocalAiSetupRequest,
    LocalAiStatusResponse,
)
from core.local_ai_sidecar import shutdown_sidecar, sidecar_snapshot
from core.runtime import data_root

SETUP_LOCK, _CANCEL_EVENT = threading.Lock(), threading.Event()
_SNAP_STATE: dict[str, LocalAiRunState] = {"ready": "ready", "starting": "waking", "error": "error"}


def get_status(root: Path | None = None) -> LocalAiStatusResponse:
    base = root or data_root()
    pkey, ram = _cat.detect_platform_key(), physical_ram_gb()
    rec = _cat.recommend_model_for_ram(ram)
    installed, rt_bin = _paths.list_installed_builtin_models(base), _paths.runtime_binary_path(base)
    state, snap = _paths.load_local_ai_state(base), sidecar_snapshot()
    active_id = state.active_model_id if state.active_model_id in installed else (installed[0] if installed else "")
    threads, ctx, _ = _cat.compute_runtime_limits(ram, state.profile, _cat.MODEL_BY_ID.get(active_id) or rec)
    offline_ready = rt_bin is not None and bool(installed)
    run_state: LocalAiRunState = "downloading" if SETUP_LOCK.locked() else ("not_installed" if not offline_ready else _SNAP_STATE.get(str(snap["status"]), "sleeping"))
    used_mb, free_gb = _paths.disk_usage_summary(base)
    presets = [
        LocalAiPresetView(id=p.id, tier=p.tier, label_key=p.label_key, size_gb=round(p.size_bytes / 1024**3, 1), min_ram_gb=p.min_ram_gb, installed=p.id in installed, recommended=p.id == rec.id)
        for p in _cat.MODEL_PRESETS
    ]
    return LocalAiStatusResponse(
        supported=pkey is not None, platform_key=pkey or "", ram_gb=ram, low_ram_warning=0 < ram < 6,
        runtime_installed=rt_bin is not None, installed_models=installed, active_model_id=active_id,
        recommended_model_id=rec.id, recommended_size_gb=round(rec.size_bytes / 1024**3, 1),
        disk_used_mb=used_mb, free_disk_gb=free_gb, state=run_state, offline_ready=offline_ready,
        gpu_active=bool(snap["gpu_active"]) and not state.force_cpu, profile=state.profile,
        idle_minutes=state.idle_minutes, ctx_size=ctx, threads=threads, force_cpu=state.force_cpu,
        last_error=str(snap["last_error"]), presets=presets,
    )


def cancel_setup() -> bool:
    _CANCEL_EVENT.set()
    return True


def stream_setup_events(req: LocalAiSetupRequest, root: Path | None = None, *, client: httpx.Client | None = None) -> Iterator[dict[str, object]]:
    """Yield live progress/done/error dicts while downloading & verifying runtime + model."""
    base, pkey = root or data_root(), _cat.detect_platform_key()
    if pkey is None:
        raise HTTPException(status_code=400, detail="Built-in Private AI is not available for this CPU architecture. You can use Ollama, Cloud APIs, or Instant Search.")
    preset = _cat.recommend_model_for_ram(physical_ram_gb()) if req.model_id == "recommended" else _cat.MODEL_BY_ID.get(req.model_id)
    if preset is None:
        raise HTTPException(status_code=400, detail="Choose one of the approved Built-in Private AI tiers.")
    if not SETUP_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Built-in Private AI setup is already running.")
    _CANCEL_EVENT.clear()
    asset = _cat.RUNTIME_ASSETS[pkey]
    events: queue.Queue[dict[str, object] | None] = queue.Queue()

    def _emit(stage: str, pct: int, dl_mb: float, tot_mb: float) -> None:
        events.put({"event": "progress", "data": {"stage": stage, "pct": pct, "downloaded_mb": dl_mb, "total_mb": tot_mb}})

    def _worker() -> None:
        try:
            need_rt, m_path = _paths.runtime_binary_path(base) is None, _paths.model_file_path(preset.id, base)
            need_model = not (m_path.is_file() and not m_path.is_symlink())
            _paths.check_disk_space((asset.size_bytes if need_rt else 0) + (preset.size_bytes if need_model else 0), base)
            if need_rt:
                dl_archive = _paths.runtime_root(base) / "downloads" / asset.archive_name
                _inst.download_verified_file(asset.url, dl_archive, asset.sha256, asset.size_bytes, "runtime", on_progress=_emit, cancel_event=_CANCEL_EVENT, client=client)
                _emit("extract", 100, round(asset.size_bytes / 1048576, 1), round(asset.size_bytes / 1048576, 1))
                _inst.safe_extract_archive(dl_archive, _paths.bin_dir(base, asset.release_tag), asset.binary_name)
                dl_archive.unlink(missing_ok=True)
            if need_model:
                _inst.download_verified_file(preset.url, m_path, preset.sha256, preset.size_bytes, "model", on_progress=_emit, cancel_event=_CANCEL_EVENT, client=client)
            cur = _paths.load_local_ai_state(base)
            prof = req.profile or cur.profile
            _, _, def_idle = _cat.compute_runtime_limits(physical_ram_gb(), prof, preset)
            _paths.save_local_ai_state(cur.model_copy(update={"active_model_id": preset.id, "installed_runtime_tag": asset.release_tag, "profile": prof, "idle_minutes": def_idle if req.profile else cur.idle_minutes}), base)
            events.put({"event": "done", "data": get_status(base).model_dump(mode="json")})
        except InterruptedError:
            events.put({"event": "error", "data": {"detail": "Setup cancelled. You can resume anytime where you left off."}})
        except (OSError, ValueError, httpx.HTTPError) as exc:
            events.put({"event": "error", "data": {"detail": str(exc) or "Download could not be completed. Check your internet connection and disk space."}})
        finally:
            SETUP_LOCK.release()
            events.put(None)

    threading.Thread(target=_worker, name="realm-local-ai-setup", daemon=True).start()
    while (ev := events.get()) is not None:
        yield ev


def update_config(upd: LocalAiConfigUpdate, root: Path | None = None) -> LocalAiStatusResponse:
    base, cur, patch = root or data_root(), _paths.load_local_ai_state(root), {}
    if upd.profile is not None:
        patch["profile"] = upd.profile
        if upd.idle_minutes is None:
            patch["idle_minutes"] = 5 if upd.profile == "eco" else 10
    if upd.idle_minutes is not None:
        patch["idle_minutes"] = upd.idle_minutes
    if upd.force_cpu is not None:
        patch["force_cpu"] = upd.force_cpu
    if upd.active_model_id is not None:
        if upd.active_model_id and upd.active_model_id not in _cat.MODEL_BY_ID:
            raise HTTPException(status_code=400, detail="Unknown Built-in Private AI model tier.")
        patch["active_model_id"] = upd.active_model_id
    if patch:
        _paths.save_local_ai_state(cur.model_copy(update=patch), base)
        shutdown_sidecar()
    return get_status(base)


def uninstall_runtime(root: Path | None = None) -> dict[str, object]:
    if SETUP_LOCK.locked():
        raise HTTPException(status_code=409, detail="Cancel the active download before removing Built-in Private AI.")
    base = root or data_root()
    shutdown_sidecar()
    return {"freed_mb": _paths.remove_local_ai_files(base), "status": get_status(base).model_dump(mode="json")}
