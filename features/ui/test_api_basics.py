"""Basic read-only UI search API contracts."""

from fastapi.testclient import TestClient

from features.ui.app import app

client = TestClient(app)


def test_get_api_search_returns_results() -> None:
    response = client.get("/api/search?q=vertical+slice")
    assert response.status_code == 200
    assert len(response.json()["results"]) > 0


def test_get_api_search_tag_only_returns_rag_results() -> None:
    response = client.get("/api/search?q=&tag=rag")
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) > 0
    for result in data["results"]:
        assert "rag" in result["chunk"]["tags"]


def test_get_api_search_with_tutor_returns_answer() -> None:
    response = client.get("/api/search?q=pgvector&ask_tutor=true")
    assert response.status_code == 200
    tutor = response.json()["tutor"]
    assert tutor is not None and tutor["answer"]
    assert tutor["cited_titles"] == list(dict.fromkeys(tutor["cited_titles"]))


def test_get_api_guides_returns_grouped_guides() -> None:
    guides = client.get("/api/guides").json()
    assert isinstance(guides, list) and len(guides) > 0
    assert {"doc_id", "title", "tags", "sections"} <= set(guides[0].keys())
    rag_guides = client.get("/api/guides?tag=rag").json()
    assert len(rag_guides) > 0 and all("rag" in g["tags"] for g in rag_guides)
