"""Managed llama-server sidecar supervisor: lazy launch, idle sleep, GPU fallback & shutdown."""

from __future__ import annotations

import atexit
import secrets
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException

from core import local_ai_catalog as _cat
from core import local_ai_os as _os
from core import local_ai_paths as _paths
from core.cancellation import check_cancelled
from core.hardware import physical_ram_gb
from core.logging_config import get_logger
from core.runtime import data_root

_LOG, _LOCK = get_logger("local_ai"), threading.RLock()
_GPU_ERR_MARKERS = ("vulkan", "vkcreate", "metal", "ggml_metal", "out of memory", "cuda", "failed to allocate")
_STATE: dict[str, Any] = {
    "proc": None, "port": 0, "token": "", "model_id": "", "profile": "eco", "force_cpu": False,
    "ctx_size": 4096, "threads": 4, "gpu_active": True, "status": "stopped", "last_used": 0.0,
    "busy": 0, "last_error": "", "job_handle": None, "log_fh": None, "pid_path": None, "reaper": None,
}


def _pick_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])
def active_sidecar_context_size(model_id: str = "", root: Path | None = None) -> int:
    with _LOCK:
        if _STATE["status"] == "ready" and (not model_id or _STATE["model_id"] == model_id):
            return int(_STATE["ctx_size"])
    state = _paths.load_local_ai_state(root)
    preset = _cat.MODEL_BY_ID.get(model_id) or _cat.MODEL_BY_ID.get(state.active_model_id) or _cat.recommend_model_for_ram(physical_ram_gb())
    return _cat.compute_runtime_limits(physical_ram_gb(), state.profile, preset)[1]
def sidecar_snapshot() -> dict[str, Any]:
    with _LOCK:
        proc = _STATE["proc"]
        status = _STATE["status"] if (proc is not None and proc.poll() is None) else ("error" if _STATE["last_error"] else "stopped")
        return {"status": status, "gpu_active": bool(_STATE["gpu_active"]), "ctx_size": int(_STATE["ctx_size"]), "threads": int(_STATE["threads"]), "model_id": str(_STATE["model_id"]), "last_error": str(_STATE["last_error"])}
def mark_sidecar_busy(delta: int) -> None:
    with _LOCK:
        _STATE["busy"], _STATE["last_used"] = max(0, int(_STATE["busy"]) + delta), time.monotonic()
def shutdown_sidecar() -> bool:
    """Terminate any running llama-server sidecar process and free RAM immediately."""
    with _LOCK:
        proc, pid_path, job, log_fh = _STATE["proc"], _STATE["pid_path"], _STATE["job_handle"], _STATE["log_fh"]
        _STATE.update({"proc": None, "port": 0, "token": "", "status": "stopped", "job_handle": None, "log_fh": None, "pid_path": None})
    _os.terminate_process(proc, pid_path=pid_path, job_handle=job)
    if log_fh is not None:
        try:
            log_fh.close()
        except OSError:
            pass
    return proc is not None
def _idle_reaper_loop() -> None:
    while True:
        time.sleep(15.0)
        with _LOCK:
            if _STATE["proc"] is None or _STATE["status"] != "ready" or int(_STATE["busy"]) > 0:
                continue
            expired = (time.monotonic() - float(_STATE["last_used"])) >= max(1, _paths.load_local_ai_state().idle_minutes) * 60.0
        if expired:
            _LOG.info("Built-in Private AI idle timeout reached; sleeping to free RAM")
            shutdown_sidecar()


def _wait_ready(proc: subprocess.Popen[Any], port: int, token: str, timeout: float = 60.0) -> bool:
    deadline, url, headers = time.monotonic() + timeout, f"http://127.0.0.1:{port}/health", {"Authorization": f"Bearer {token}"}
    with httpx.Client(trust_env=False, follow_redirects=False, timeout=2.0) as client:
        while time.monotonic() < deadline:
            check_cancelled()
            if proc.poll() is not None:
                return False
            try:
                if client.get(url, headers=headers).status_code == 200:
                    return True
            except httpx.HTTPError:
                pass
            time.sleep(0.25)
    return False


def _launch_once(binary: Path, model_path: Path, reasoning: bool, ctx: int, threads: int, use_cpu: bool, root: Path) -> tuple[str, str]:
    port, token = _pick_loopback_port(), secrets.token_urlsafe(24)
    log_path, pid_path = root / "logs" / "local-ai.log", _paths.runtime_root(root) / "llama-server.pid"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = log_path.open("wb")
    args = _cat.build_llama_server_args(str(binary), str(model_path), port, token, ctx, threads, reasoning, use_cpu)
    proc = subprocess.Popen(args, stdout=log_fh, stderr=subprocess.STDOUT, cwd=str(binary.parent), **_os.popen_platform_kwargs())
    job = _os.attach_windows_job_object(int(getattr(proc, "_handle", 0))) if hasattr(proc, "_handle") else None
    _os.write_pid_file(pid_path, proc.pid)
    with _LOCK:
        _STATE.update({"proc": proc, "port": port, "token": token, "ctx_size": ctx, "threads": threads, "gpu_active": not use_cpu, "status": "starting", "job_handle": job, "log_fh": log_fh, "pid_path": pid_path, "last_error": ""})
    if _wait_ready(proc, port, token):
        with _LOCK:
            _STATE.update({"status": "ready", "last_used": time.monotonic()})
            if _STATE["reaper"] is None or not _STATE["reaper"].is_alive():
                t = threading.Thread(target=_idle_reaper_loop, name="realm-local-ai-reaper", daemon=True)
                t.start()
                _STATE["reaper"] = t
        return f"http://127.0.0.1:{port}/v1/chat/completions", token
    shutdown_sidecar()
    tail = log_path.read_text(encoding="utf-8", errors="ignore")[-800:].lower() if log_path.is_file() else ""
    if not use_cpu and any(m in tail for m in _GPU_ERR_MARKERS):
        _LOG.warning("GPU startup failed for Built-in Private AI; retrying in CPU safe mode")
        return _launch_once(binary, model_path, reasoning, min(ctx, 4096), threads, True, root)
    msg = "Built-in Private AI stopped unexpectedly (low memory or graphics issue). Try Quiet/Eco mode or a smaller model."
    with _LOCK:
        _STATE["last_error"] = msg
    raise HTTPException(status_code=503, detail=msg)


def ensure_sidecar_running(model_id: str | None = None, *, root: Path | None = None) -> tuple[str, str, str]:
    """Ensure llama-server is running for the requested installed model; return (url, token, model_id)."""
    base = root or data_root()
    state, installed, binary = _paths.load_local_ai_state(base), _paths.list_installed_builtin_models(base), _paths.runtime_binary_path(base)
    if binary is None or not installed:
        raise HTTPException(status_code=503, detail="Built-in Private AI is not set up yet. Open Settings → AI & Voice to install it.")
    target_id = model_id if (model_id and model_id in installed) else (state.active_model_id if state.active_model_id in installed else installed[0])
    preset = _cat.MODEL_BY_ID[target_id]
    threads, ctx, _ = _cat.compute_runtime_limits(physical_ram_gb(), state.profile, preset)
    with _LOCK:
        proc = _STATE["proc"]
        if proc is not None and proc.poll() is None and _STATE["status"] == "ready" and _STATE["model_id"] == target_id and _STATE["profile"] == state.profile and _STATE["force_cpu"] == state.force_cpu:
            _STATE["last_used"] = time.monotonic()
            return f"http://127.0.0.1:{_STATE['port']}/v1/chat/completions", str(_STATE["token"]), target_id
    shutdown_sidecar()
    with _LOCK:
        _STATE.update({"model_id": target_id, "profile": state.profile, "force_cpu": state.force_cpu})
    url, token = _launch_once(binary, _paths.model_file_path(target_id, base), preset.supports_reasoning, ctx, threads, state.force_cpu, base)
    return url, token, target_id


atexit.register(shutdown_sidecar)
