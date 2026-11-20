"""Files and transport bodies are rejected before conversion or persistence."""

import base64
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from features.ui import upload_guard


@pytest.mark.parametrize("endpoint", ["/api/upload", "/api/anonymize/preview"])
def test_exact_fifteen_mib_file_ceiling(area_client: TestClient, tmp_path: Path, endpoint: str) -> None:
    assert upload_guard.MAX_UPLOAD_BYTES == 15 * 1024 * 1024
    oversized = b"x" * (upload_guard.MAX_UPLOAD_BYTES + 1)
    response = area_client.post(endpoint, files={"file": ("large.txt", oversized, "text/plain")})
    assert response.status_code == 413 and "15 MB" in response.json()["detail"]
    assert not (tmp_path / "knowledge_base/large.md").exists()


@pytest.mark.parametrize("base64_input", [False, True])
def test_json_batch_size_checked_before_any_file_is_saved(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, base64_input: bool) -> None:
    monkeypatch.setattr(upload_guard, "MAX_UPLOAD_BYTES", 100)
    too_big = {"content_base64": base64.b64encode(b"x" * 101).decode()} if base64_input else {"content": "x" * 101}
    response = area_client.post("/api/upload", json={"files": [{"filename": "first.md", "content": "# First\n## Body\nSmall"}, {"filename": "large.txt", **too_big}]})
    assert response.status_code == 413
    assert not (tmp_path / "knowledge_base/first.md").exists()
    assert not (tmp_path / "knowledge_base/large.md").exists()
    assert area_client.post("/api/upload", json={"filename": "equal.md", "content": "# Equal\n## Body\n" + "x" * 84}).status_code == 200


@pytest.mark.parametrize("endpoint", ["/api/upload", "/api/anonymize/preview"])
def test_declared_and_streamed_body_limits(area_client: TestClient, monkeypatch: pytest.MonkeyPatch, endpoint: str) -> None:
    response = area_client.post(endpoint, content=b"tiny", headers={"content-length": str(500 * 1024 * 1024), "content-type": "application/json"})
    assert response.status_code == 413
    monkeypatch.setattr(upload_guard, "MAX_BATCH_BYTES", 256)
    monkeypatch.setattr(upload_guard, "MAX_UPLOAD_BYTES", 128)
    response = area_client.post(endpoint, content=iter([b'x' * 129, b'x' * 129]), headers={"content-type": "application/json"})
    assert response.status_code == 413


def test_preview_text_bytes_and_normal_small_upload(area_client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(upload_guard, "MAX_UPLOAD_BYTES", 100)
    assert area_client.post("/api/anonymize/preview", json={"text": "é" * 51}).status_code == 413
    preview = area_client.post("/api/anonymize/preview", json={"text": "a@example.invalid", "filename": "note.txt"})
    assert preview.status_code == 200 and preview.json()["counts_by_type"]["EMAIL"] == 1
    upload = area_client.post("/api/upload", files={"file": ("tiny.md", b"# Small\n## Body\nSmall content.", "text/markdown")})
    assert upload.status_code == 200 and upload.json()["doc_count"] == 2
    assert area_client.post("/api/upload", json={"filename": "bad.md", "content_base64": "a"}).status_code == 400
