"""Upload, privacy, and local audio endpoint regression tests."""

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.contracts import WorkspaceConfig
from features.ui import app as ui_app
from features.ui import audio_routes, workspace

client = TestClient(ui_app.app)


def test_post_api_upload_and_audio_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(workspace, "resolve_safe_knowledge_dir", lambda _d, _r=tmp_path, create=False: tmp_path)
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(knowledge_dir="tmp_kb"))
    res = client.post("/api/upload", files=[("files", ("CV_Jon_Doe_2026.txt", b"Pulsars are magnetized neutron stars. Contact Jon Doe at bob@example.de.", "text/plain"))], data={"anonymize": "false"})
    assert res.status_code == 200 and res.json()["redacted_count"] == 0
    anon_res = client.post("/api/guides/cv_jon_doe_2026/anonymize").json()
    assert anon_res["doc_id"] == "cv_jon_doe_2026" and anon_res["redacted_count"] >= 3
    scrubbed_doc = (tmp_path / "cv_jon_doe_2026.md").read_text(encoding="utf-8")
    assert "[REDACTED_EMAIL]" in scrubbed_doc and "[REDACTED_NAME]" in scrubbed_doc and "Tags: uploaded" not in scrubbed_doc
    del_res = client.delete("/api/guides/cv_jon_doe_2026").json()
    assert del_res == {"doc_id": "cv_jon_doe_2026", "deleted": True} and not (tmp_path / "cv_jon_doe_2026.md").exists()
    assert audio_routes.filter_human_voices(["Zoey", "Grub the Ogre", "Vyrmathrax the Ancient"]) == ["default", "Zoey"]
    assert audio_routes.strip_voice_label("Zoey (US Female)") == "Zoey"
    audio_st = client.get("/api/audio/status").json()
    assert {"whisper_available", "tts_models"} <= set(audio_st.keys()) and isinstance(audio_st["tts_models"], list)
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)
    tr_res = client.post("/api/audio/transcribe", content=b"fake-audio").json()
    assert tr_res["fallback"] == "unavailable" and tr_res["text"] == ""


def test_get_root_returns_search_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "AI Engineering Knowledge Engine" in response.text
    assert "Where should we start?" in response.text
    assert "--background: #04060F" in response.text
    assert "--surface-raised: #0B1020" in response.text
    assert "--accent: #4BB8E8" in response.text
    assert "Summarize the key points across my documents" in response.text
    assert "search" in response.text.lower()


def test_get_favicon_and_static_logo_return_ok() -> None:
    assert client.get("/favicon.ico").status_code == 200
    logo_response = client.get("/static/logo-512.png")
    assert logo_response.status_code == 200 and logo_response.headers["content-type"] == "image/png"


def test_progressive_loading_and_abort_controller_in_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Synthesizing answer with " in response.text
    assert "from-[#0B1020] via-[#162240] to-[#0B1020] animate-pulse rounded-lg h-4" in response.text
    assert "AbortController" in response.text


def test_get_api_models_returns_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ui_app, "WORKSPACE_CONFIG", WorkspaceConfig(strict_local_only=False))
    response = client.get("/api/models?provider=openai")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "openai" and len(data["models"]) > 0


def test_get_and_post_api_workspace_and_system_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    st = client.get("/api/system-status").json()
    assert {"ollama_online", "ollama_models", "chat_models", "embedding_models", "audio_models", "has_nomic_embed", "retrieval_tier", "is_first_run", "doc_count"} <= set(st.keys())
    data = client.get("/api/workspace").json()
    assert data["doc_count"] >= 3 and "knowledge_base" in data["available_dirs"]
    bad_response = client.post("/api/workspace", json={"app_title": "Test", "hero_greeting": "Hi", "search_placeholder": "Search...", "knowledge_dir": "../outside"})
    assert bad_response.status_code == 400
    monkeypatch.setattr(workspace, "WORKSPACE_FILE", tmp_path / "workspace.json")
    orig_resolve = workspace.resolve_safe_knowledge_dir
    monkeypatch.setattr(workspace, "resolve_safe_knowledge_dir", lambda d, repo_root=tmp_path, create=False: orig_resolve(d, repo_root=tmp_path, create=create))
    create_res = client.post("/api/workspace", json={"app_title": "Homework Tutor", "hero_greeting": "Ready?", "search_placeholder": "Ask...", "knowledge_dir": "my_homework"})
    assert create_res.status_code == 200 and (tmp_path / "my_homework").is_dir()
    ui_app.WORKSPACE_CONFIG, ui_app.INDEX = WorkspaceConfig(), []
    monkeypatch.setattr(workspace, "resolve_safe_knowledge_dir", orig_resolve)


def test_upload_infers_topics_instead_of_file_format(area_client: TestClient) -> None:
    content = "# Python Architecture\nTags: uploaded\n\n## Engineering\nPython engineering finance recipes. Python architecture engineering finance recipes."
    response = area_client.post("/api/upload", json={"filename": "study.md", "content": content, "tags": "uploaded,pdf,docx,txt"})
    assert response.status_code == 200 and response.json()["uploaded_titles"] == ["Python Architecture"]
    guide = next(g for g in area_client.get("/api/guides").json() if g["doc_id"] == "study")
    assert set(guide["tags"]) == {"python", "architecture", "engineering", "finance", "recipes"}
    nodes = area_client.get("/api/graph?all_areas=false").json()["nodes"]
    assert len(nodes) >= 8 and any(n.get("section_index") == 0 and n.get("doc_id") == "study" for n in nodes)
    assert not {"uploaded", "pdf", "docx", "txt"}.intersection(t["name"] for t in response.json()["tags"])


def test_startup_repairs_placeholder_tags_in_inactive_areas(area_client: TestClient, tmp_path: Path) -> None:
    folder = tmp_path / "test"
    folder.mkdir()
    document = folder / "legacy.md"
    document.write_text("# Engineering\nTags: uploaded\n\n## Python\nPython architecture engineering finance recipes.", encoding="utf-8")
    binary = folder / "not-yet-imported.pdf"
    binary.write_bytes(b"unrelated invalid binary")
    with TestClient(ui_app.app) as booted:
        assert booted.get("/api/workspace").status_code == 200
    assert "Tags: uploaded" not in document.read_text()
    binary.unlink()
    assert area_client.post("/api/workspace", json={"knowledge_dir": "test"}).status_code == 200
    assert "python" in area_client.get("/api/guides").json()[0]["tags"]
