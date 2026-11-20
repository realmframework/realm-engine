"""Explicit, allowlisted local model downloads; no prompts, keys or document text are sent."""

from collections.abc import Callable
from threading import Lock

import httpx
from fastapi import APIRouter, HTTPException, Request

from core.contracts import WorkspaceConfig
from features.ui import workspace
from features.ui.hardware import physical_ram_gb

PULL_URL = "http://127.0.0.1:11434/api/pull"
EMBEDDING_MODEL = "nomic-embed-text:v1.5"
PULL_LOCK = Lock()


def recommended_model(ram_gb: int) -> str:
    return "qwen3:8b" if ram_gb >= 16 else "qwen2.5:3b"


def build_router(config: Callable[[], WorkspaceConfig], refresh: Callable[[], None]) -> APIRouter:
    router = APIRouter()

    @router.post("/api/system/pull-model")
    def pull_model(payload: dict[str, str], request: Request) -> dict[str, object]:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
        ram = physical_ram_gb()
        selected = payload.get("model", "recommended")
        selected = recommended_model(ram) if selected == "recommended" else selected
        allowed = {"qwen2.5:3b", EMBEDDING_MODEL, recommended_model(ram)}
        if selected not in allowed:
            raise HTTPException(status_code=400, detail="Choose the recommended local model for this computer.")
        if not PULL_LOCK.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="A model download is already running. Please wait for it to finish.")
        downloaded: list[str] = []
        try:
            with httpx.Client(trust_env=False, follow_redirects=False, timeout=httpx.Timeout(1800, connect=2)) as client:
                for name in dict.fromkeys([selected, EMBEDDING_MODEL]):
                    response = client.post(PULL_URL, json={"name": name, "model": name, "stream": False})
                    response.raise_for_status()
                    result = response.json()
                    if not isinstance(result, dict) or result.get("status") != "success":
                        raise ValueError("Download did not complete")
                    downloaded.append(name)
            refresh()
            return {"installed_models": downloaded, "recommended_model": selected, "ram_gb": ram}
        except httpx.ConnectError as exc:
            raise HTTPException(status_code=503, detail="Open Ollama first, then try Download Recommended Local AI again. You can keep using Search & Anonymize now.") from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="Download is taking longer than expected. Ollama may still be downloading; check installed models before retrying.") from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise HTTPException(status_code=502, detail="Local model download did not finish. Check Ollama, your internet connection and free disk space, then retry.") from exc
        finally:
            PULL_LOCK.release()

    return router
