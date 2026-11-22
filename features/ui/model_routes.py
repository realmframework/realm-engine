"""Explicit, allowlisted local model downloads; no prompts, keys or document text are sent."""

from collections.abc import Callable
from threading import Lock

import httpx
from fastapi import APIRouter, HTTPException, Request

from core.contracts import WorkspaceConfig
from core.runtime import is_loopback_url, ollama_base_url
from features.ui import workspace
from features.ui.hardware import physical_ram_gb

EMBEDDING_MODEL = "nomic-embed-text:v1.5"
PULL_LOCK = Lock()


def pull_url() -> str:
    return f"{ollama_base_url()}/api/pull"


def build_router(config: Callable[[], WorkspaceConfig], refresh: Callable[[], None]) -> APIRouter:
    router = APIRouter()

    @router.post("/api/system/pull-model")
    def pull_model(payload: dict[str, str], request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
        ram = physical_ram_gb()
        requested = (payload.get("model") or "embedding").strip()
        selected = EMBEDDING_MODEL if requested in {"recommended", "embedding", EMBEDDING_MODEL} else requested
        if selected != EMBEDDING_MODEL:
            raise HTTPException(status_code=400, detail="Only the local Ollama search helper (nomic-embed-text:v1.5) can be pulled here; pull chat models directly in Ollama.")
        if not PULL_LOCK.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="A model download is already running. Please wait for it to finish.")
        downloaded: list[str] = []
        try:
            target_url = pull_url()
            with httpx.Client(trust_env=not is_loopback_url(target_url), follow_redirects=False, timeout=httpx.Timeout(1800, connect=2)) as client:
                response = client.post(target_url, json={"name": selected, "model": selected, "stream": False})
                response.raise_for_status()
                result = response.json()
                if not isinstance(result, dict) or result.get("status") != "success":
                    raise ValueError("Download did not complete")
                downloaded.append(selected)
            refresh()
            return {"installed_models": downloaded, "embedding_model": selected, "ram_gb": ram}
        except httpx.ConnectError as exc:
            raise HTTPException(status_code=503, detail="Open Ollama first, then try downloading the search helper again. You can keep using Search & Anonymize now.") from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Download is taking longer than expected. Ollama may still be downloading; check installed models before retrying.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="Local model download did not finish. Check Ollama, your internet connection and free disk space, then retry.") from exc
        finally:
            PULL_LOCK.release()

    return router
