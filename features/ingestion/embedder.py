"""Resilient zero-Ollama, incremental batch, and cloud embedding helper."""

import httpx

from core.contracts import KnowledgeChunk
from core.secrets import get_api_key

DEFAULT_OLLAMA_EMBED_URL = "http://127.0.0.1:11434/api/embed"
DEFAULT_EMBED_MODEL = "nomic-embed-text:v1.5"
OLLAMA_CONNECT_TIMEOUT = 1.5
OLLAMA_BATCH_TIMEOUT = 15.0
CLOUD_EMBED_TIMEOUT = 5.0
EMBED_BATCH_SIZE = 32

CLOUD_EMBED_DEFAULTS: dict[str, tuple[str, str, str]] = {
    "openai": ("https://api.openai.com/v1/embeddings", "text-embedding-3-small", "OPENAI_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1/embeddings", "mistral-embed", "MISTRAL_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/embeddings", "gemini-embedding-2", "GEMINI_API_KEY"),
}

_LAST_FAILED_POST: object | None = None


def reset_ollama_status() -> None:
    """Reset the cached Ollama offline failure state."""
    global _LAST_FAILED_POST
    _LAST_FAILED_POST = None


def is_ollama_offline() -> bool:
    """Return True if the last local Ollama embedding request failed."""
    return _LAST_FAILED_POST is httpx.post


def _extract_vectors(payload: dict[str, object]) -> list[list[float]]:
    embeddings = payload.get("embeddings")
    if isinstance(embeddings, list):
        return [[float(x) for x in vec] for vec in embeddings if isinstance(vec, list)]
    data = payload.get("data")
    if isinstance(data, list):
        result: list[list[float]] = []
        for item in data:
            if isinstance(item, dict) and isinstance(item.get("embedding"), list):
                result.append([float(x) for x in item["embedding"]])
        return result
    return []


def embed_batch(
    texts: list[str],
    provider: str = "ollama",
    api_key: str | None = None,
    ollama_url: str = DEFAULT_OLLAMA_EMBED_URL,
    model: str = DEFAULT_EMBED_MODEL,
) -> list[list[float]]:
    """Generate embeddings for a batch of texts, returning ``[]`` on failure or offline."""
    global _LAST_FAILED_POST
    if not texts:
        return []
    if provider in CLOUD_EMBED_DEFAULTS:
        url, default_model, _ = CLOUD_EMBED_DEFAULTS[provider]
        key = get_api_key(provider, api_key)
        if not key:
            return []
        use_model = default_model if model == DEFAULT_EMBED_MODEL else model
        try:
            res = httpx.post(
                url=url,
                json={"model": use_model, "input": texts if len(texts) > 1 else texts[0]},
                headers={"Authorization": f"Bearer {key}"},
                timeout=CLOUD_EMBED_TIMEOUT,
            )
            return _extract_vectors(res.json())
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []

    if provider != "ollama" or _LAST_FAILED_POST is httpx.post:
        return []
    payload: dict[str, object] = {"model": model, "input": texts if len(texts) > 1 else texts[0]}
    timeout = OLLAMA_BATCH_TIMEOUT if len(texts) > 1 else OLLAMA_CONNECT_TIMEOUT
    try:
        try:
            response = httpx.post(url=ollama_url, json=payload, timeout=timeout)
        except TypeError:
            response = httpx.post(url=ollama_url, json=payload)
        _LAST_FAILED_POST = None
        return _extract_vectors(response.json())
    except (httpx.HTTPError, ValueError, KeyError):
        _LAST_FAILED_POST = httpx.post
        return []


def embed_text(
    text: str,
    provider: str = "ollama",
    api_key: str | None = None,
    ollama_url: str = DEFAULT_OLLAMA_EMBED_URL,
    model: str = DEFAULT_EMBED_MODEL,
) -> list[float]:
    """Generate an embedding vector, falling back to ``[]`` when offline or unconfigured."""
    if not text.strip():
        return []
    vectors = embed_batch([text], provider=provider, api_key=api_key, ollama_url=ollama_url, model=model)
    return vectors[0] if vectors else []


def embed_chunk(
    chunk: KnowledgeChunk,
    ollama_url: str = DEFAULT_OLLAMA_EMBED_URL,
    model: str = DEFAULT_EMBED_MODEL,
    provider: str = "ollama",
    api_key: str | None = None,
) -> KnowledgeChunk:
    """Populate the embedding vector for ``chunk`` via local Ollama or cloud embeddings."""
    vector = embed_text(chunk.content, provider=provider, api_key=api_key, ollama_url=ollama_url, model=model)
    return chunk.model_copy(update={"embedding": vector})


def hydrate_embeddings(
    chunks: list[KnowledgeChunk],
    cached: list[KnowledgeChunk],
    embed_missing: bool = False,
    provider: str = "ollama",
    api_key: str | None = None,
    model: str = DEFAULT_EMBED_MODEL,
) -> list[KnowledgeChunk]:
    """Preserve cached embeddings for unchanged chunks and optionally batch-embed missing ones."""
    cache_map = {(c.id, c.title, c.content): c.embedding for c in cached if c.embedding}
    hydrated = [
        c.model_copy(update={"embedding": cache_map[(c.id, c.title, c.content)]})
        if (c.id, c.title, c.content) in cache_map
        else c
        for c in chunks
    ]
    if not embed_missing:
        return hydrated
    missing = [idx for idx, c in enumerate(hydrated) if not c.embedding and c.content.strip()]
    for start in range(0, len(missing), EMBED_BATCH_SIZE):
        batch_indices = missing[start : start + EMBED_BATCH_SIZE]
        texts = [f"{hydrated[i].title}\n{hydrated[i].content}" for i in batch_indices]
        vectors = embed_batch(texts, provider=provider, api_key=api_key, model=model)
        if len(vectors) != len(batch_indices):
            break
        for idx, vec in zip(batch_indices, vectors, strict=True):
            if vec:
                hydrated[idx] = hydrated[idx].model_copy(update={"embedding": vec})
    return hydrated
