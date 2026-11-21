"""Unit tests for the tutor agent service, Kimi K3.1 Pro params, and model discovery."""

import json
from typing import Any

import httpx
import pytest

from core.contracts import KnowledgeChunk, SearchResult, TutorConfig
from features.tutor_agent.models_discovery import discover_models
from features.tutor_agent.providers import (
    FALLBACK_MODELS,
    call_provider,
    list_provider_models,
)
from features.tutor_agent.service import (
    ask_tutor,
    build_tutor_messages,
    fallback_tutor_response,
)


class _FakeChatResponse:
    def __init__(self, content: str, payload: dict[str, Any] | None = None) -> None:
        self._payload = payload if payload is not None else {"message": {"content": content}}

    def json(self) -> dict[str, Any]:
        return self._payload


def make_result(title: str = "Hybrid Search") -> SearchResult:
    return SearchResult(chunk=KnowledgeChunk(id="chunk-001", title=title, file_path="knowledge/hybrid.md", content="BM25 and dense retrieval", tags=["rag"]), score=0.9)


def test_build_tutor_messages_and_fallbacks() -> None:
    messages = build_tutor_messages("How does hybrid search work?", [make_result()])
    assert len(messages) == 2 and messages[0]["role"] == "system" and "Hybrid Search" in messages[1]["content"]
    empty_msgs = build_tutor_messages("How does hybrid search work?", [])
    assert "knowledge_gap_detected" in empty_msgs[0]["content"] and "topics to study next" in empty_msgs[1]["content"]
    fallback = fallback_tutor_response("How does retrieval work?", [make_result("Hybrid Search"), make_result("Vector Search"), make_result("Dense Retrieval")])
    assert fallback.knowledge_gap_detected is False and fallback.cited_titles == ["Hybrid Search", "Vector Search", "Dense Retrieval"]
    assert "Based on the retrieved knowledge" in fallback.answer and "Dense Retrieval" in fallback.answer


def test_ask_tutor_valid_and_partial_json_and_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    content = json.dumps({"answer": "Hybrid search combines BM25 and dense retrieval."})

    def fake_post(url: str, json: dict[str, object], timeout: float = 90.0) -> _FakeChatResponse:
        return _FakeChatResponse(content)

    monkeypatch.setattr(httpx, "post", fake_post)
    response = ask_tutor("How does hybrid search work?", [make_result()])
    assert response.answer == "Hybrid search combines BM25 and dense retrieval." and response.knowledge_gap_detected is False

    for code, expected in ((401, "rejected credentials"), (429, "rate limit")):
        def status_post(url: str, json: dict[str, object], headers: dict[str, str] | None = None, timeout: float = 30.0, code: int = code) -> httpx.Response:
            return httpx.Response(code, request=httpx.Request("POST", url))

        monkeypatch.setattr(httpx, "post", status_post)
        err_resp = ask_tutor("Test?", [make_result()], TutorConfig(provider="kimi", api_key="bad"))
        assert err_resp.knowledge_gap_detected is True and expected in err_resp.answer.lower()

    for error in (httpx.ConnectError("refused"), ValueError("invalid")):
        def failing_post(url: str, json: dict[str, object], timeout: float = 90.0, error: BaseException = error) -> _FakeChatResponse:
            raise error

        monkeypatch.setattr(httpx, "post", failing_post)
        assert ask_tutor("How does hybrid search work?", []).knowledge_gap_detected is True


def test_call_provider_ollama_anthropic_kimi_and_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_post(url: str, json: dict[str, object], headers: dict[str, str] | None = None, timeout: float = 30.0) -> _FakeChatResponse:
        captured.update(url=url, body=json, headers=headers)
        if "anthropic" in url:
            return _FakeChatResponse("json-text", {"content": [{"type": "text", "text": "json-text"}]})
        if "11434" in url:
            return _FakeChatResponse('{"answer": "ok"}')
        return _FakeChatResponse('{"answer": "ok"}', {"choices": [{"message": {"content": '{"answer": "ok"}'}}]})

    monkeypatch.setattr(httpx, "post", fake_post)
    assert call_provider([{"role": "user", "content": "Hi"}], TutorConfig(provider="ollama")) == '{"answer": "ok"}'
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"

    assert call_provider([{"role": "system", "content": "Sys"}, {"role": "user", "content": "Hi"}], TutorConfig(provider="anthropic", api_key="ak")) == "json-text"
    assert captured["headers"]["x-api-key"] == "ak"

    assert call_provider([{"role": "user", "content": "Hi"}], TutorConfig(provider="kimi", api_key="kk")) == '{"answer": "ok"}'
    assert captured["url"] == "https://api.moonshot.ai/v1/chat/completions" and captured["headers"]["Authorization"] == "Bearer kk"
    assert "temperature" not in captured["body"] and captured["body"]["reasoning_effort"] == "low"
    assert captured["body"]["model"] == "kimi-k3.1-pro"

    call_provider([{"role": "user", "content": "Hi"}], TutorConfig(provider="deepseek", api_key="dk"))
    assert captured["url"] == "https://api.deepseek.com/chat/completions" and captured["body"]["temperature"] == 0.2


def test_list_provider_models_uses_real_endpoints_and_filters(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_urls: list[str] = []

    def fake_ollama_get(url: str, timeout: float = 5.0) -> _FakeChatResponse:
        seen_urls.append(url)
        return _FakeChatResponse("", {"models": [{"name": "nomic-embed-text:v1.5"}, {"name": "phonon-tts:latest"}, {"name": "llama3:8b"}, {"name": "qwen3:8b"}]})

    monkeypatch.setattr(httpx, "get", fake_ollama_get)
    assert list_provider_models("ollama") == ["qwen3:8b", "llama3:8b"]
    assert seen_urls[-1] == "http://127.0.0.1:11434/api/tags"
    classified = discover_models(["nomic-embed-text:v1.5", "gemini-embedding-2", "phonon-tts", "whisper-large", "qwen3:8b"])
    assert classified["chat_models"] == ["qwen3:8b"] and classified["embedding_models"] == ["nomic-embed-text:v1.5", "gemini-embedding-2"]
    assert classified["audio_models"] == ["phonon-tts", "whisper-large"]

    def fake_cloud_get(url: str, headers: dict[str, str] | None = None, timeout: float = 10.0) -> _FakeChatResponse:
        seen_urls.append(url)
        return _FakeChatResponse("", {"data": [{"id": "models/kimi-k3.1-pro"}, {"id": "models/text-embedding-3-small"}]})

    monkeypatch.setattr(httpx, "get", fake_cloud_get)
    assert list_provider_models("openai", api_key="ok") == ["kimi-k3.1-pro"]
    assert seen_urls[-1] == "https://api.openai.com/v1/models"
    assert list_provider_models("kimi", api_key="kk") == ["kimi-k3.1-pro"]
    assert seen_urls[-1] == "https://api.moonshot.ai/v1/models"
    assert list_provider_models("gemini", api_key="gk") == ["kimi-k3.1-pro"]
    assert seen_urls[-1] == "https://generativelanguage.googleapis.com/v1beta/openai/models"
    assert list_provider_models("openai") == FALLBACK_MODELS["openai"]


def test_stream_prompt_prioritizes_agent_identity_and_preserves_live_web_urls() -> None:
    from features.tutor_agent.prompt_builder import build_stream_messages

    big_vault = [
        SearchResult(chunk=KnowledgeChunk(id=f"v-{i}", title=f"Vault {i}", file_path=f"v{i}.md", content="A" * 5000, tags=[]), score=0.9)
        for i in range(8)
    ]
    web_hit = SearchResult(
        chunk=KnowledgeChunk(id="web-1", title="Web — Chip Huyen", file_path="https://huyenchip.com/", url="https://huyenchip.com/", content="AI Engineering author site.", tags=["web"]),
        score=0.62,
    )
    persona = "[ACTIVE AGENT PERSONA: Saga — Lead Knowledge Agent]\nYou are Saga, the Lead Knowledge Agent inside REALM Engine."
    msgs = build_stream_messages("Find Chip Huyen's site", [*big_vault, web_hit], persona_instruction=persona, web_search_requested=True)
    assert msgs[0]["content"].startswith("[ACTIVE AGENT PERSONA: Saga")
    assert "LIVE WEB SEARCH ACTIVE" in msgs[0]["content"]
    assert "<live_web_search_results>" in msgs[1]["content"]
    assert "URL: https://huyenchip.com/" in msgs[1]["content"]
    assert msgs[1]["content"].index("<live_web_search_results>") < msgs[1]["content"].index("<untrusted_document_context>")
    empty_web = build_stream_messages("Latest news", [], persona_instruction=persona, web_search_requested=True)
    assert "LIVE WEB SEARCH ATTEMPTED" in empty_web[0]["content"]
