"""Server-side provider admission for the current workspace privacy policy."""

from fastapi import HTTPException

from core.contracts import WorkspaceConfig


def require_local(config: WorkspaceConfig, provider: str | None, model: str | None = None) -> None:
    if config.strict_local_only and ((provider or "ollama") != "ollama" or "cloud" in (model or "").lower()):
        raise HTTPException(status_code=403, detail="Strict Local-Only Lock is active. Use a local Ollama model or disable the lock in Settings.")
