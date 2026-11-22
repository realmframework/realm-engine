"""Route & service tests for the features/local_ai vertical slice."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import local_ai_catalog, local_ai_installer, local_ai_paths, local_ai_sidecar
from features.local_ai import router as local_ai_router
from features.local_ai import service as local_ai_service


def _build_fake_archive(archive_name: str, binary_name: str) -> bytes:
    buf = io.BytesIO()
    if archive_name.endswith(".zip"):
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(f"bin/{binary_name}", b"FAKE-BIN")
    else:
        with tarfile.open(fileobj=buf, mode="w:gz") as tf:
            info = tarfile.TarInfo(f"bin/{binary_name}")
            info.size, info.mode = 8, 0o755
            tf.addfile(info, io.BytesIO(b"FAKE-BIN"))
    return buf.getvalue()


def test_local_ai_routes_setup_config_unload_and_uninstall(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = FastAPI()
    app.include_router(local_ai_router.build_router(lambda: tmp_path))
    client = TestClient(app)

    pkey = local_ai_catalog.detect_platform_key() or "macos-arm64"
    monkeypatch.setattr(local_ai_catalog, "detect_platform_key", lambda: pkey)
    monkeypatch.setattr(local_ai_paths, "detect_platform_key", lambda: pkey)
    monkeypatch.setattr(local_ai_service, "physical_ram_gb", lambda: 16)
    monkeypatch.setattr(local_ai_paths, "check_disk_space", lambda *_a, **_k: None)

    st0 = client.get("/api/local-ai/status")
    assert st0.status_code == 200
    body0 = st0.json()
    assert body0["supported"] is True and body0["offline_ready"] is False
    assert body0["recommended_model_id"] == "balanced-qwen35-9b" and len(body0["presets"]) == 5

    asset = local_ai_catalog.RUNTIME_ASSETS[pkey]
    preset = local_ai_catalog.MODEL_BY_ID["ultra-qwen35-2b"]
    rt_bytes = _build_fake_archive(asset.archive_name, asset.binary_name)
    model_bytes = b"GGUF-FAKE-MODEL-BYTES" * 64
    monkeypatch.setitem(
        local_ai_catalog.RUNTIME_ASSETS,
        pkey,
        asset.model_copy(update={"sha256": hashlib.sha256(rt_bytes).hexdigest(), "size_bytes": len(rt_bytes)}),
    )
    monkeypatch.setitem(
        local_ai_catalog.MODEL_BY_ID,
        preset.id,
        preset.model_copy(update={"sha256": hashlib.sha256(model_bytes).hexdigest(), "size_bytes": len(model_bytes)}),
    )

    def respond(req: httpx.Request) -> httpx.Response:
        if asset.archive_name in str(req.url):
            return httpx.Response(200, content=rt_bytes)
        return httpx.Response(200, content=model_bytes)

    orig_client = httpx.Client
    monkeypatch.setattr(local_ai_installer.httpx, "Client", lambda **_kw: orig_client(transport=httpx.MockTransport(respond)))

    setup_res = client.post("/api/local-ai/setup/stream", json={"model_id": "ultra-qwen35-2b"})
    assert setup_res.status_code == 200 and "event: progress" in setup_res.text and "event: done" in setup_res.text
    done_line = [ln for ln in setup_res.text.splitlines() if ln.startswith("data:")][-1][5:].strip()
    done_payload = json.loads(done_line)
    assert done_payload["offline_ready"] is True and done_payload["active_model_id"] == "ultra-qwen35-2b"

    cfg_res = client.post("/api/local-ai/config", json={"profile": "performance"})
    assert cfg_res.status_code == 200 and cfg_res.json()["profile"] == "performance" and cfg_res.json()["idle_minutes"] == 10
    assert client.post("/api/local-ai/config", json={"active_model_id": "not-a-real-tier"}).status_code == 400
    assert client.post("/api/local-ai/cancel-setup").json() == {"cancelled": True}

    unloaded = client.post("/api/local-ai/unload")
    assert unloaded.status_code == 200 and unloaded.json()["status"]["state"] == "sleeping"

    removed = client.delete("/api/local-ai/runtime")
    assert removed.status_code == 200 and removed.json()["status"]["offline_ready"] is False
    local_ai_sidecar.shutdown_sidecar()
