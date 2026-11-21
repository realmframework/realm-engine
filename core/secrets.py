"""App-level local API key storage (0600 permissions under ./data/) and .env fallback."""

import json
import os
from pathlib import Path
from threading import RLock

from core.db import atomic_write_text, backup_corrupt_file
from core.runtime import bundle_root, data_root, is_frozen

SECRETS_FILE = data_root() / "secrets.json"
LOCK = RLock()
ENV_VARS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "kimi": "MOONSHOT_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "xai": "XAI_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "elevenlabs": "ELEVENLABS_API_KEY",
    "ollama_web": "OLLAMA_API_KEY",
}


def load_dotenv_files(paths: list[Path] | None = None) -> None:
    """Load key=value pairs from optional local .env files without overriding shell env."""
    defaults = [data_root() / ".env"] if is_frozen() else [bundle_root() / ".env", data_root() / ".env"]
    candidates = paths if paths is not None else defaults
    for path in candidates:
        if not path.is_file() or path.is_symlink():
            continue
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key_clean = key.strip().removeprefix("export ").strip()
                val_clean = value.strip()
                if len(val_clean) >= 2 and val_clean[0] == val_clean[-1] and val_clean[0] in {"'", '"'}:
                    val_clean = val_clean[1:-1]
                if key_clean and val_clean:
                    os.environ.setdefault(key_clean, val_clean)
        except OSError:
            continue


def _read_store(*, recover_corrupt: bool = False) -> dict[str, str]:
    if SECRETS_FILE.is_symlink() or SECRETS_FILE.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Secrets storage cannot be a symbolic link")
    if not SECRETS_FILE.is_file():
        return {}
    try:
        raw = json.loads(SECRETS_FILE.read_text(encoding="utf-8"))
    except ValueError:
        if recover_corrupt:
            backup_corrupt_file(SECRETS_FILE, mode=0o600)
            return {}
        raise
    if not isinstance(raw, dict):
        if recover_corrupt:
            backup_corrupt_file(SECRETS_FILE, mode=0o600)
        return {}
    return {str(k): str(v).strip() for k, v in raw.items() if k in ENV_VARS and isinstance(v, str) and v.strip()}


def _write_store(store: dict[str, str]) -> None:
    if SECRETS_FILE.is_symlink() or SECRETS_FILE.with_suffix(".json.tmp").is_symlink():
        raise ValueError("Secrets storage cannot be a symbolic link")
    atomic_write_text(SECRETS_FILE, json.dumps(store, indent=2), mode=0o600)


def _mask_key(key: str) -> str:
    return f"…{key[-4:]}" if len(key) >= 10 else "saved"


def get_api_key(provider: str, explicit: str | None = None) -> str | None:
    """Resolve a provider key: explicit request value -> app ./data/secrets.json -> env/.env."""
    if explicit and explicit.strip():
        return explicit.strip()
    if provider not in ENV_VARS:
        return None
    with LOCK:
        try:
            saved = _read_store().get(provider)
            if saved:
                return saved
        except (OSError, ValueError):
            pass
    env_val = os.environ.get(ENV_VARS[provider], "").strip()
    return env_val or None


def key_status_map() -> dict[str, dict[str, object]]:
    """Return masked configuration status for every provider without exposing raw secrets."""
    with LOCK:
        try:
            store = _read_store()
        except (OSError, ValueError):
            store = {}
    status: dict[str, dict[str, object]] = {}
    for provider, env_var in ENV_VARS.items():
        if saved := store.get(provider):
            status[provider] = {"configured": True, "source": "app", "hint": _mask_key(saved)}
        elif env_val := os.environ.get(env_var, "").strip():
            status[provider] = {"configured": True, "source": "env", "hint": _mask_key(env_val)}
        else:
            status[provider] = {"configured": False, "source": "none", "hint": ""}
    return status


def save_api_key(provider: str, api_key: str) -> dict[str, dict[str, object]]:
    """Persist a provider key in app-level 0600 storage and return updated masked status."""
    if provider not in ENV_VARS:
        raise ValueError(f"Unsupported provider: {provider}")
    cleaned = api_key.strip()
    with LOCK:
        store = _read_store(recover_corrupt=True)
        if cleaned:
            store[provider] = cleaned
        else:
            store.pop(provider, None)
        _write_store(store)
    return key_status_map()


def delete_api_keys(provider: str | None = None) -> dict[str, dict[str, object]]:
    """Remove one or all saved app-level API keys and return updated masked status."""
    with LOCK:
        store = _read_store(recover_corrupt=True)
        if provider:
            if provider not in ENV_VARS:
                raise ValueError(f"Unsupported provider: {provider}")
            store.pop(provider, None)
        else:
            store.clear()
        _write_store(store)
    return key_status_map()
