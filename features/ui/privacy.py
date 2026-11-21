"""Server-side provider admission for the current workspace privacy policy."""

import os

from fastapi import HTTPException

from core.contracts import WorkspaceConfig
from core.runtime import is_loopback_url, ollama_base_url


def require_local(config: WorkspaceConfig, provider: str | None, model: str | None = None) -> None:
    if not config.strict_local_only:
        return
    if (provider or "ollama") != "ollama" or "cloud" in (model or "").lower():
        raise HTTPException(status_code=403, detail="Strict Local-Only Lock is active. Use a local Ollama model or disable the lock in Settings.")
    if not is_loopback_url(ollama_base_url()) and os.environ.get("REALM_ALLOW_REMOTE_OLLAMA", "").strip() != "1":
        raise HTTPException(status_code=403, detail="Strict Local-Only Lock blocks non-loopback OLLAMA_HOST targets. Set REALM_ALLOW_REMOTE_OLLAMA=1 to override.")
