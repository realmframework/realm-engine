"""Model capability classification and filtering for local Ollama and cloud providers."""

EMBEDDING_PREFIXES = (
    "nomic-embed",
    "mxbai-embed",
    "bge-",
    "all-minilm",
    "text-embedding",
    "mistral-embed",
    "gemini-embedding",
)
AUDIO_PREFIXES = (
    "whisper",
    "phonon",
    "kokoro",
    "piper",
    "tts-",
)


def is_embedding_model(model_name: str) -> bool:
    """Return True if ``model_name`` is an embedding model rather than a chat LLM."""
    lower = model_name.strip().lower()
    return any(lower.startswith(prefix) for prefix in EMBEDDING_PREFIXES) or "embed" in lower


def is_audio_model(model_name: str) -> bool:
    """Return True if ``model_name`` is an STT or TTS audio model."""
    lower = model_name.strip().lower()
    return any(lower.startswith(prefix) for prefix in AUDIO_PREFIXES)


def discover_models(model_names: list[str]) -> dict[str, list[str]]:
    """Classify a list of raw model names into ``chat_models``, ``embedding_models``, and ``audio_models``."""
    chat_models: list[str] = []
    embedding_models: list[str] = []
    audio_models: list[str] = []
    for raw in model_names:
        name = raw.strip()
        if not name:
            continue
        if is_embedding_model(name):
            embedding_models.append(name)
        elif is_audio_model(name):
            audio_models.append(name)
        else:
            chat_models.append(name)
    chat_models.sort(key=lambda m: (0 if m.lower().startswith("qwen3:") else 1 if m.lower().startswith("qwen2.5:") else 2))
    return {
        "chat_models": chat_models,
        "embedding_models": embedding_models,
        "audio_models": audio_models,
    }


def filter_chat_models(model_names: list[str]) -> list[str]:
    """Return only valid chat LLMs with recommended local defaults prioritized when present."""
    return discover_models(model_names)["chat_models"]
