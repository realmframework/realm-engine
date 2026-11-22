"""Unit tests for Built-in Private AI catalog, verified installer, sidecar & local routing."""

from __future__ import annotations

import hashlib
import http.server
import io
import socketserver
import subprocess
import sys
import tarfile
import threading
import zipfile
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException

from core import (
    ai_stream,
    context_meter,
    local_ai_catalog,
    local_ai_installer,
    local_ai_paths,
    local_ai_sidecar,
    model_routing,
)
from core.agent_presets import AgentPersona
from core.contracts import WorkspaceConfig


def test_catalog_ram_tiers_platforms_and_thermal_limits() -> None:
    assert local_ai_catalog.recommend_model_for_ram(4).id == "ultra-qwen35-2b"
    assert local_ai_catalog.recommend_model_for_ram(8).id == "compact-qwen35-4b"
    assert local_ai_catalog.recommend_model_for_ram(16).id == "balanced-qwen35-9b"
    assert local_ai_catalog.recommend_model_for_ram(24).id == "advanced-ministral3-14b"
    assert local_ai_catalog.recommend_model_for_ram(32).id == "flagship-muse-glimmer-30b"
    assert local_ai_catalog.detect_platform_key("darwin", "arm64") == "macos-arm64"
    assert local_ai_catalog.detect_platform_key("win32", "AMD64") == "win-vulkan-x64"
    assert local_ai_catalog.detect_platform_key("linux", "x86_64") == "linux-vulkan-x64"
    preset = local_ai_catalog.MODEL_BY_ID["balanced-qwen35-9b"]
    assert local_ai_catalog.compute_runtime_limits(16, "eco", preset, cores=8) == (4, 4096, 5)
    assert local_ai_catalog.compute_runtime_limits(16, "performance", preset, cores=8) == (6, 8192, 10)
    assert local_ai_catalog.compute_runtime_limits(4, "performance", preset, cores=8)[1] == 2048


def test_installer_resume_sha256_host_allowlist_and_zip_slip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = b"0123456789abcdef" * 32
    digest, dest = hashlib.sha256(payload).hexdigest(), tmp_path / "models" / "demo.gguf"
    part = dest.parent / "demo.gguf.part"
    part.parent.mkdir(parents=True)
    part.write_bytes(payload[:64])

    def respond(req: httpx.Request) -> httpx.Response:
        if req.headers.get("Range") == "bytes=64-":
            return httpx.Response(206, content=payload[64:], headers={"Content-Length": str(len(payload) - 64)})
        return httpx.Response(200, content=payload)

    hf_url = "https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/resolve/main/Qwen3.5-4B-Q4_K_M.gguf"
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        assert local_ai_installer.download_verified_file(hf_url, dest, digest, len(payload), "model", client=client).read_bytes() == payload
        assert not part.exists()
        with pytest.raises(ValueError, match="approved official release host"):
            local_ai_installer.download_verified_file("https://evil.example.com/x.gguf", tmp_path / "bad.gguf", digest, len(payload), "model", client=client)
        bad_dest = tmp_path / "bad_hash.gguf"
        with pytest.raises(ValueError, match="Integrity verification failed"):
            local_ai_installer.download_verified_file(hf_url, bad_dest, "0" * 64, len(payload), "model", client=client)
        assert not bad_dest.exists() and not (bad_dest.parent / "bad_hash.gguf.part").exists()

    monkeypatch.setattr(local_ai_paths.shutil, "disk_usage", lambda _p: SimpleNamespace(free=100))
    with pytest.raises(ValueError, match="Not enough free disk space"):
        local_ai_paths.check_disk_space(10**9, tmp_path)

    evil_zip = tmp_path / "evil.zip"
    with zipfile.ZipFile(evil_zip, "w") as zf:
        zf.writestr("../escape.txt", "boom")
    with pytest.raises(ValueError, match="Unsafe archive entry path"):
        local_ai_installer.safe_extract_archive(evil_zip, tmp_path / "out_zip", "llama-server.exe")

    good_tar = tmp_path / "good.tar.gz"
    with tarfile.open(good_tar, "w:gz") as tf:
        info = tarfile.TarInfo("build/bin/llama-server")
        info.size, info.mode = 10, 0o755
        tf.addfile(info, io.BytesIO(b"#!/bin/sh\n"))
    assert local_ai_installer.safe_extract_archive(good_tar, tmp_path / "out_tar", "llama-server").name == "llama-server"


def test_sidecar_lifecycle_gpu_fallback_and_policy_routing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls, ready_hits = [], {"n": 0}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                ready_hits["n"] += 1
                self.send_response(503 if ready_hits["n"] == 1 else 200)
                self.end_headers()
        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    httpd = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        bin_file = local_ai_paths.bin_dir(tmp_path) / ("llama-server.exe" if sys.platform == "win32" else "llama-server")
        bin_file.parent.mkdir(parents=True, exist_ok=True)
        bin_file.write_text("#!/bin/sh\n", encoding="utf-8")
        m_file = local_ai_paths.model_file_path("compact-qwen35-4b", tmp_path)
        m_file.parent.mkdir(parents=True, exist_ok=True)
        m_file.write_bytes(b"GGUF")
        monkeypatch.setattr(local_ai_sidecar, "_pick_loopback_port", lambda: port)
        monkeypatch.setattr(local_ai_sidecar, "physical_ram_gb", lambda: 16)
        monkeypatch.setattr(local_ai_catalog, "detect_physical_cores", lambda: 8)

        class _FakeProc:
            def __init__(self, fail_vulkan: bool, log_fh: object) -> None:
                self.pid, self._dead = 424242, fail_vulkan
                if fail_vulkan and hasattr(log_fh, "write"):
                    log_fh.write(b"ggml_vulkan: vkCreateInstance failed\n")  # type: ignore[union-attr]
                    log_fh.flush()  # type: ignore[union-attr]
            def poll(self) -> int | None:
                return 1 if self._dead else None
            def terminate(self) -> None:
                self._dead = True
            def wait(self, timeout: float | None = None) -> int:
                return 0

        def fake_popen(args: list[str], **kw: object) -> subprocess.Popen[bytes]:
            calls.append(args)
            return _FakeProc(len(calls) == 1, kw.get("stdout"))  # type: ignore[return-value]

        monkeypatch.setattr(local_ai_sidecar.subprocess, "Popen", fake_popen)
        url, token, mid = local_ai_sidecar.ensure_sidecar_running("compact-qwen35-4b", root=tmp_path)
        assert url == f"http://127.0.0.1:{port}/v1/chat/completions" and len(token) >= 16 and mid == "compact-qwen35-4b"
        assert len(calls) == 2 and "--device" in calls[1] and "none" in calls[1] and "auto" in calls[1]
        assert context_meter.model_context_window("builtin", "compact-qwen35-4b") == 4096
        assert local_ai_sidecar.shutdown_sidecar() is True
    finally:
        local_ai_sidecar.shutdown_sidecar()
        httpd.shutdown()
        httpd.server_close()

    strict_cfg = WorkspaceConfig(strict_local_only=True)
    assert ai_stream.is_local_policy_satisfied(strict_cfg, "builtin", "compact-qwen35-4b") is True
    assert ai_stream.is_local_policy_satisfied(strict_cfg, "openai", "gpt-4o-mini") is False
    saga = AgentPersona(id="saga", name="Saga", role="Analyst", tagline="t", instructions="i")
    assert model_routing.resolve_agent_model(saga, strict_cfg, "builtin", "compact-qwen35-4b", None)[:2] == ("builtin", "compact-qwen35-4b")
    with pytest.raises(HTTPException):
        model_routing.resolve_agent_model(saga, strict_cfg, "openai", "gpt-4o-mini", None)
