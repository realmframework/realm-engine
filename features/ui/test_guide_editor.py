"""Tests for Phase 2: Save Answer as Guide, In-App Markdown Editor, and Highlight-to-Ask."""

from pathlib import Path

from fastapi.testclient import TestClient


def test_create_read_and_edit_guide_roundtrip(area_client: TestClient, tmp_path: Path) -> None:
    created = area_client.post(
        "/api/guides/create",
        json={
            "title": "Lisbeth Audit Findings",
            "content": "## Summary\nKey numbers verified.\n",
            "tags": "synthesis, lisbeth",
            "subfolder": "research/2026",
            "citations": ["Shared Guide"],
        },
    )
    assert created.status_code == 200
    body = created.json()
    doc_id = body["doc_id"]
    assert doc_id == "research/2026/lisbeth_audit_findings"
    saved_file = tmp_path / "knowledge_base/research/2026/lisbeth_audit_findings.md"
    assert saved_file.is_file()
    disk_text = saved_file.read_text(encoding="utf-8")
    assert 'title: "Lisbeth Audit Findings"' in disk_text and "## Sources" in disk_text and "- Shared Guide" in disk_text

    # Duplicate title creates unique numbered filename rather than overwriting
    dup = area_client.post(
        "/api/guides/create",
        json={"title": "Lisbeth Audit Findings", "content": "Second draft", "subfolder": "research/2026"},
    )
    assert dup.status_code == 200 and dup.json()["doc_id"] == "research/2026/lisbeth_audit_findings-2"

    # Read raw & update in-app -> immediately re-indexed
    raw = area_client.get(f"/api/guides/{doc_id}/raw")
    assert raw.status_code == 200 and "Key numbers verified." in raw.json()["raw_markdown"]
    updated = area_client.put(
        f"/api/guides/{doc_id}/raw",
        json={"content": "# Lisbeth Audit Updated\n\n## Findings\nUnique updated emerald token.\n"},
    )
    assert updated.status_code == 200
    assert updated.json()["guide"]["title"] == "Lisbeth Audit Updated"
    hits = area_client.get("/api/search?q=emerald+token&retrieval_mode=lexical").json()["results"]
    assert hits and any("emerald token" in h["chunk"]["content"] for h in hits)


def test_guide_editor_rejects_symlinks_empty_and_zero_workspace(area_client: TestClient, tmp_path: Path) -> None:
    assert area_client.put("/api/guides/shared/raw", json={"content": "   "}).status_code == 400
    assert area_client.post("/api/guides/create", json={"title": "", "content": "Body"}).status_code == 400
    secret = tmp_path / "outside.md"
    secret.write_text("# Secret\n", encoding="utf-8")
    (tmp_path / "knowledge_base/link.md").symlink_to(secret)
    assert area_client.get("/api/guides/link/raw").status_code == 404
    assert area_client.delete("/api/workspace/knowledge_base").status_code == 200
    assert area_client.post("/api/guides/create", json={"title": "Orphan", "content": "Body"}).status_code == 400
    html = area_client.get("/").text
    for marker in ('id="save-guide-modal" closedby="any"', 'id="reader-selection-pill" hidden', 'id="sel-explain-btn"', "id='guide-edit-btn'"):
        assert marker in html
