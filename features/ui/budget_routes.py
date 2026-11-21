"""Local budget reservations, reset, and app-level API key management routes."""

from collections.abc import Callable

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from core import secrets
from core.contracts import WorkspaceConfig
from features.ui import workspace


def build_router(config: Callable[[], WorkspaceConfig], snapshot: Callable[..., dict[str, object]], reset: Callable[[], None]) -> APIRouter:
    router = APIRouter()

    def status(request: Request) -> JSONResponse:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            return JSONResponse(snapshot(active.daily_cloud_request_limit, active.daily_budget_usd_limit), headers={"Cache-Control": "no-store"})

    @router.get("/api/budget")
    def get_budget(request: Request) -> JSONResponse:
        return status(request)

    @router.post("/api/budget/reset")
    def reset_counter(request: Request, payload: dict[str, bool]) -> JSONResponse:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
            if payload.get("confirm") is not True:
                raise HTTPException(status_code=400, detail="Confirm the budget counter reset")
            try:
                reset()
            except (OSError, ValueError) as exc:
                raise HTTPException(status_code=503, detail="Budget state could not be reset") from exc
            return status(request)

    @router.get("/api/keys/status")
    def get_key_status(request: Request) -> JSONResponse:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
        return JSONResponse({"keys": secrets.key_status_map()}, headers={"Cache-Control": "no-store"})

    @router.post("/api/keys")
    def save_key(request: Request, payload: dict[str, str]) -> JSONResponse:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
        provider = str(payload.get("provider") or "").strip().lower()
        api_key = str(payload.get("api_key") or "")
        try:
            updated = secrets.save_api_key(provider, api_key)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except OSError as exc:
            raise HTTPException(status_code=400, detail="Could not save API key to local storage") from exc
        return JSONResponse({"keys": updated}, headers={"Cache-Control": "no-store"})

    @router.delete("/api/keys")
    def delete_keys(request: Request, provider: str | None = None) -> JSONResponse:
        with workspace.STATE_LOCK:
            workspace.require_area(request, config())
        try:
            updated = secrets.delete_api_keys(provider.strip().lower() if provider else None)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except OSError as exc:
            raise HTTPException(status_code=400, detail="Could not remove API key from local storage") from exc
        return JSONResponse({"keys": updated}, headers={"Cache-Control": "no-store"})

    return router
