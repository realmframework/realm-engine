"""Resilient zero-Ollama, incremental batch, and cloud embedding helper."""

import time
from threading import Lock

import httpx

from core.contracts import KnowledgeChunk
from core.runtime import is_loopback_url, ollama_base_url
from core.secrets import get_api_key

DEFAULT_OLLAMA_EMBED_URL = f"{ollama_base_url()}/api/embed"
DEFAULT_EMBED_MODEL = "nomic-embed-text:v1.5"
OLLAMA_CONNECT_TIMEOUT, OLLAMA_BATCH_TIMEOUT, CLOUD_EMBED_TIMEOUT = 1.5, 15.0, 5.0
OLLAMA_SINGLE_TIMEOUT = httpx.Timeout(connect=OLLAMA_CONNECT_TIMEOUT, read=10.0, write=5.0, pool=2.0)
EMBED_BATCH_SIZE, MAX_EMBED_CHARS, OLLAMA_RETRY_COOLDOWN_SEC = 32, 6000, 30.0
_ORIG_POST = httpx.post
_STATE_LOCK = Lock()

CLOUD_EMBED_DEFAULTS: dict[str, tuple[str, str, str]] = {
    "openai": ("https://api.openai.com/v1/embeddings", "text-embedding-3-small", "OPENAI_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1/embeddings", "mistral-embed", "MISTRAL_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/embeddings", "gemini-embedding-2", "GEMINI_API_KEY"),
}
_LAST_FAILED_POST: object | None = None
_OFFLINE_UNTIL: float = 0.0


def reset_ollama_status() -> None:
    """Reset the cached Ollama offline cooldown state."""
    global _LAST_FAILED_POST, _OFFLINE_UNTIL
    with _STATE_LOCK:
        _LAST_FAILED_POST, _OFFLINE_UNTIL = None, 0.0


def is_ollama_offline() -> bool:
    """Return True if local Ollama embeddings are inside their failure cooldown window."""
    with _STATE_LOCK:
        return _LAST_FAILED_POST is httpx.post and time.monotonic() < _OFFLINE_UNTIL


def _extract_vectors(payload: object) -> list[list[float]]:
    if not isinstance(payload, dict):
        return []
    if isinstance(embeddings := payload.get("embeddings"), list):
        return [[float(x) for x in vec] for vec in embeddings if isinstance(vec, list)]
    if isinstance(data := payload.get("data"), list):
        items = [item for item in data if isinstance(item, dict) and isinstance(item.get("embedding"), list)]
        if all(isinstance(item.get("index"), int) for item in items):
            items.sort(key=lambda item: int(item["index"]))
        return [[float(x) for x in item["embedding"]] for item in items]
    return []


def _check_status(response: object) -> None:
    status = getattr(response, "status_code", None)
    if isinstance(status, int) and status >= 400:
        if callable(checker := getattr(response, "raise_for_status", None)):
            checker()
        raise httpx.HTTPError(f"Embedding endpoint returned HTTP {status}")


def embed_batch(texts: list[str], provider: str = "ollama", api_key: str | None = None, ollama_url: str = DEFAULT_OLLAMA_EMBED_URL, model: str = DEFAULT_EMBED_MODEL) -> list[list[float]]:
    """Generate embeddings for a batch of texts, returning ``[]`` on failure or offline."""
    global _LAST_FAILED_POST, _OFFLINE_UNTIL
    if not texts:
        return []
    trimmed = [t[:MAX_EMBED_CHARS] for t in texts]
    if provider in CLOUD_EMBED_DEFAULTS:
        url, default_model, _ = CLOUD_EMBED_DEFAULTS[provider]
        if not (key := get_api_key(provider, api_key)):
            return []
        use_model = default_model if model == DEFAULT_EMBED_MODEL else model
        req_body = {"model": use_model, "input": trimmed if len(trimmed) > 1 else trimmed[0]}
        try:
            if httpx.post is _ORIG_POST:
                with httpx.Client(follow_redirects=False, timeout=CLOUD_EMBED_TIMEOUT) as client:
                    res = client.post(url, json=req_body, headers={"Authorization": f"Bearer {key}"})
            else:
                res = httpx.post(url=url, json=req_body, headers={"Authorization": f"Bearer {key}"}, timeout=CLOUD_EMBED_TIMEOUT)
            _check_status(res)
            return _extract_vectors(res.json())
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            return []
    if provider != "ollama" or is_ollama_offline():
        return []
    payload: dict[str, object] = {"model": model, "input": trimmed if len(trimmed) > 1 else trimmed[0], "keep_alive": "30s"}
    timeout: float | httpx.Timeout = OLLAMA_BATCH_TIMEOUT if len(trimmed) > 1 else OLLAMA_SINGLE_TIMEOUT
    target_url = f"{ollama_base_url()}/api/embed" if (ollama_url == DEFAULT_OLLAMA_EMBED_URL and httpx.post is _ORIG_POST) else ollama_url
    try:
        if httpx.post is _ORIG_POST:
            with httpx.Client(trust_env=not is_loopback_url(target_url), follow_redirects=False, timeout=timeout) as client:
                response = client.post(target_url, json=payload)
        else:
            try:
                response = httpx.post(url=target_url, json=payload, timeout=OLLAMA_BATCH_TIMEOUT if len(trimmed) > 1 else OLLAMA_CONNECT_TIMEOUT)
            except TypeError:
                response = httpx.post(url=target_url, json=payload)
        _check_status(response)
        with _STATE_LOCK:
            _LAST_FAILED_POST, _OFFLINE_UNTIL = None, 0.0
        return _extract_vectors(response.json())
    except (httpx.ConnectError, httpx.ConnectTimeout):
        with _STATE_LOCK:
            _LAST_FAILED_POST, _OFFLINE_UNTIL = httpx.post, time.monotonic() + OLLAMA_RETRY_COOLDOWN_SEC
        return []
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return []


def embed_text(text: str, provider: str = "ollama", api_key: str | None = None, ollama_url: str = DEFAULT_OLLAMA_EMBED_URL, model: str = DEFAULT_EMBED_MODEL) -> list[float]:
    if not text.strip():
        return []
    vectors = embed_batch([text], provider=provider, api_key=api_key, ollama_url=ollama_url, model=model)
    return vectors[0] if vectors else []


def embed_chunk(chunk: KnowledgeChunk, ollama_url: str = DEFAULT_OLLAMA_EMBED_URL, model: str = DEFAULT_EMBED_MODEL, provider: str = "ollama", api_key: str | None = None) -> KnowledgeChunk:
    return chunk.model_copy(update={"embedding": embed_text(chunk.content, provider=provider, api_key=api_key, ollama_url=ollama_url, model=model)})


def hydrate_embeddings(chunks: list[KnowledgeChunk], cached: list[KnowledgeChunk], embed_missing: bool = False, provider: str = "ollama", api_key: str | None = None, model: str = DEFAULT_EMBED_MODEL, cached_model: str = "") -> list[KnowledgeChunk]:
    """Preserve cached embeddings for unchanged chunks (when model matches) and batch-embed missing ones."""
    model_ok = not cached_model or cached_model == model
    cache_map = {(c.id, c.title, c.content): c.embedding for c in cached if c.embedding} if model_ok else {}
    hydrated = [c.model_copy(update={"embedding": cache_map[(c.id, c.title, c.content)]}) if (c.id, c.title, c.content) in cache_map else c for c in chunks]
    if not embed_missing:
        return hydrated
    missing = [idx for idx, c in enumerate(hydrated) if not c.embedding and c.content.strip()]
    for start in range(0, len(missing), EMBED_BATCH_SIZE):
        batch_indices = missing[start : start + EMBED_BATCH_SIZE]
        texts = [f"{hydrated[i].title}\n{hydrated[i].content}"[:MAX_EMBED_CHARS] for i in batch_indices]
        vectors = embed_batch(texts, provider=provider, api_key=api_key, model=model)
        if len(vectors) == len(batch_indices):
            for idx, vec in zip(batch_indices, vectors, strict=True):
                if vec:
                    hydrated[idx] = hydrated[idx].model_copy(update={"embedding": vec})
        elif is_ollama_offline() and provider == "ollama":
            break
        elif len(batch_indices) > 1:
            for idx, txt in zip(batch_indices, texts, strict=True):
                if vec := embed_text(txt, provider=provider, api_key=api_key, model=model):
                    hydrated[idx] = hydrated[idx].model_copy(update={"embedding": vec})
                elif is_ollama_offline() and provider == "ollama":
                    break
    return hydrated
