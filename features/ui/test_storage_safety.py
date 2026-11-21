"""Regression tests for Batch 2: Atomic storage, linked-vault read-safety, binary guards, MCP & attachments."""

import io
import json
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import agent_personas, db, linked_vaults, mcp_bridge, study_ai, study_cards
from core.contracts import ChatSession
from features.ui import area_routes, chat_store


def test_corrupt_index_and_chat_persistence_never_brick_or_wipe(tmp_path: Path) -> None:
    idx = tmp_path / "index.json"
    idx.write_text("{corrupt", encoding="utf-8")
    assert db.load_chunks(idx) == []

    chats_file = tmp_path / "chats.json"
    chats_file.write_text("{corrupt json", encoding="utf-8")
    saved = chat_store.save_chat_session(ChatSession(chat_id="c1", title="New", updated_at="2026-01-01T00:00:00Z"), chats_file)
    assert saved.chat_id == "c1" and chats_file.with_suffix(".json.corrupt").is_file()

    # Partial corruption keeps healthy sessions while backing up corrupt payload
    good = ChatSession(chat_id="keep", title="Keep", updated_at="2026-01-01T00:00:00Z").model_dump()
    chats_file.write_text(json.dumps([good, {"broken": True}]), encoding="utf-8")
    chat_store.save_chat_session(ChatSession(chat_id="c2", title="Second", updated_at="2026-01-02T00:00:00Z"), chats_file)
    assert {c.chat_id for c in chat_store.load_chats(chats_file)} == {"keep", "c2"}


def test_linked_vault_read_safety_and_path_restrictions(area_client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "realm_root"
    (root / "child_dir").mkdir(parents=True)
    with pytest.raises(ValueError, match="storage directory"):
        linked_vaults.link_folder(tmp_path, root)
    with pytest.raises(ValueError, match="storage directory"):
        linked_vaults.link_folder(root / "child_dir", root)
    hidden = tmp_path / ".secret_dir"
    hidden.mkdir()
    with pytest.raises(ValueError, match="hidden"):
        linked_vaults.link_folder(hidden, root)
    target_real = tmp_path / "real_target" / "sub"
    target_real.mkdir(parents=True)
    sym_parent = tmp_path / "sym_parent"
    sym_parent.symlink_to(tmp_path / "real_target", target_is_directory=True)
    with pytest.raises(ValueError, match="symbolic links"):
        linked_vaults.link_folder(sym_parent / "sub", root)

    vault = tmp_path.parent / f"{tmp_path.name}_readonly_ext" / "External Docs"
    vault.mkdir(parents=True)
    doc = vault / "guide.md"
    doc.write_text("# External\n\n## Note\nEmail alice@example.org.\n", encoding="utf-8")
    monkeypatch.setattr(area_routes, "pick_native_folder", lambda _p="": vault)
    linked = area_client.post("/api/workspace/link-folder", json={})
    assert linked.status_code == 200
    slug = linked.json()["linked_area"]

    # Every destructive / mutating endpoint refuses linked vaults (403/409)
    assert area_client.post("/api/workspace/create", json={"name": slug, "template": "study"}).status_code == 409
    assert area_client.put("/api/guides/guide/raw", json={"content": "# Hacked"}).status_code == 403
    assert area_client.delete("/api/guides/guide").status_code == 403
    assert area_client.post("/api/guides/guide/anonymize").status_code == 403
    assert area_client.post("/api/guides/guide/move", json={"subfolder": "moved"}).status_code == 403
    assert area_client.post("/api/subfolders", json={"name": "new_sub"}).status_code == 403
    assert area_client.post("/api/compliance/scrub", json={"confirm": True}).status_code == 403
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("extra.md", "# Extra")
    assert area_client.post("/api/backup/import", files={"file": ("b.zip", buf.getvalue(), "application/zip")}).status_code == 403

    # Study cards & progress write to .vault_cache, NEVER into external vault
    assert area_client.post("/api/study/cards", json={"front": "What is X?", "back": "Y."}).status_code == 200
    assert area_client.post("/api/study/review", json={"card_id": "abc", "rating": "good"}).status_code == 200
    assert not (vault / "study_deck.json").exists() and not (vault / "study_progress.json").exists()
    assert doc.read_text(encoding="utf-8") == "# External\n\n## Note\nEmail alice@example.org.\n"


def test_binary_guide_cannot_be_overwritten_or_anonymized_in_place(area_client: TestClient, tmp_path: Path) -> None:
    pdf_path = tmp_path / "knowledge_base" / "manual.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%binary content\n")
    assert area_client.get("/api/guides/manual/raw").status_code == 400
    assert area_client.put("/api/guides/manual/raw", json={"content": "plain text"}).status_code == 400
    assert area_client.post("/api/guides/manual/anonymize").status_code == 400
    assert pdf_path.read_bytes().startswith(b"%PDF-1.4")


def test_mcp_bridge_blocks_symlinks_dotfiles_and_excluded_subfolders(tmp_path: Path) -> None:
    kb = tmp_path / "knowledge_base"
    (kb / ".obsidian").mkdir(parents=True)
    (kb / "private").mkdir()
    (kb / "public.md").write_text("# Public\nVisible text.", encoding="utf-8")
    (kb / ".obsidian" / "secret.md").write_text("# Secret\nHidden.", encoding="utf-8")
    (kb / "private" / "note.md").write_text("# Private\nExcluded.", encoding="utf-8")
    (kb / "alias.md").symlink_to(kb / "public.md")
    (tmp_path / "workspace.json").write_text(json.dumps({"knowledge_dir": "knowledge_base", "active_dirs": ["knowledge_base"], "excluded_subfolders": {"knowledge_base": ["private"]}}), encoding="utf-8")

    for bad_id in (".obsidian/secret", "alias", "private/note"):
        resp = mcp_bridge.handle_mcp_request({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "realm_read_guide", "arguments": {"doc_id": bad_id, "area": "knowledge_base"}}}, tmp_path)
        res_obj = resp.get("result") if resp else None
        assert isinstance(res_obj, dict) and res_obj.get("isError") is True
    ok = mcp_bridge.handle_mcp_request({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "realm_read_guide", "arguments": {"doc_id": "public", "area": "knowledge_base"}}}, tmp_path)
    ok_res = ok.get("result") if ok else None
    assert isinstance(ok_res, dict) and isinstance(ok_res.get("content"), list) and "Visible text." in str(ok_res["content"][0])


def test_attachments_scrub_pii_agent_empty_id_and_study_ai_parser(area_client: TestClient, tmp_path: Path) -> None:
    res = area_client.post("/api/chats/c-pii/attach", json={"name": "note.txt", "content": "Reach me at alice@example.org"})
    assert res.status_code == 200
    saved = chat_store.get_chat_session("c-pii", chat_store.area_chat_path("knowledge_base"))
    assert saved is not None and "alice@example.org" not in saved.attached_notes[0]["content"] and "[REDACTED_EMAIL]" in saved.attached_notes[0]["content"]
    assert area_client.post("/api/chats/c-pii/attach", headers={"x-knowledge-area": "other"}, json={"name": "n", "content": "hi"}).status_code == 409

    assert agent_personas.delete_agent(tmp_path, "---") is False
    parsed = study_ai.parse_generated_cards('Based on [Guide 1]: [{"front": "Q1?", "back": "A1."}] See [2].', scope="area", source_label="G")
    assert len(parsed) == 1 and parsed[0]["front"] == "Q1?"
    assert study_cards.extract_study_cards([study_cards.KnowledgeChunk(id="1", doc_id="d", title="D", file_path="d.md", content="Q: First?\nQ: Second?\nA: Real answer.", tags=[])])
