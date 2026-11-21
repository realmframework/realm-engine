"""Active-recall flashcard deck, AI card generation, custom cards, and spaced-repetition routes."""

from collections.abc import AsyncIterator, Callable
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core import study_ai, study_cards
from core.contracts import KnowledgeChunk, TutorConfig, WorkspaceConfig
from core.linked_vaults import cache_study_path
from core.scope import matches_scope
from features.ui import route_helpers, workspace
from features.ui.privacy import require_local

StreamMessagesFn = Callable[..., AsyncIterator[dict[str, object]]]
def _study_paths(area_name: str) -> tuple[Path, Path]:
    return cache_study_path(area_name, study_ai.DECK_FILENAME, workspace.REPO_ROOT), cache_study_path(area_name, study_cards.PROGRESS_FILENAME, workspace.REPO_ROOT)
def build_router(config: Callable[[], WorkspaceConfig], chunks: Callable[[], list[KnowledgeChunk]], stream_messages: StreamMessagesFn | None = None) -> APIRouter:
    router = APIRouter()
    @router.get("/api/study/deck")
    def get_study_deck(request: Request, doc_id: str | None = None, subfolder: str | None = None, limit: int = 24) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.active_dirs:
                raise HTTPException(status_code=400, detail="Create or link a workspace to generate study cards.")
            bounded, (deck_path, prog_path) = max(1, min(60, int(limit))), _study_paths(active.knowledge_dir)
            s_key = study_ai.scope_key(doc_id, subfolder, active.active_dirs)
            saved = study_ai.load_saved_decks(deck_path).get(s_key, [])
            cards, mode = (saved[:bounded], "ai") if saved else (study_cards.extract_study_cards(chunks(), doc_id=doc_id, subfolder=subfolder, limit=bounded), "quick")
            return {"area": active.knowledge_dir, "deck_mode": mode, **study_cards.enrich_deck_with_progress(cards, study_cards.load_study_progress(prog_path))}

    @router.post("/api/study/generate")
    async def generate_ai_deck(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key"), x_request_id: str | None = Header(default=None, alias="x-request-id")) -> dict[str, object]:
        if stream_messages is None:
            raise HTTPException(status_code=503, detail="AI flashcard generation is unavailable.")
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        doc_id = str(body.get("doc_id") or "").strip() or None
        subfolder = str(body["subfolder"]).strip() if isinstance(body.get("subfolder"), str) else None
        try:
            count = max(3, min(20, int(str(body.get("count") or 8))))
        except (ValueError, TypeError):
            count = 8
        raw_style = str(body.get("style") or "concepts").strip().lower()
        style = raw_style if raw_style in {"concepts", "exam", "applied"} else "concepts"
        provider, model = str(body.get("provider") or "ollama").strip().lower(), str(body.get("model") or "").strip() or None

        def _prep() -> tuple[WorkspaceConfig, list[KnowledgeChunk], Path, Path, str, str, TutorConfig]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace first.")
                require_local(active, provider, model)
                scoped = [ch for ch in chunks() if matches_scope(ch, doc_id, subfolder)]
                if not scoped:
                    raise HTTPException(status_code=400, detail="No documents found in this scope to study.")
                deck_path, prog_path = _study_paths(active.knowledge_dir)
                s_key = study_ai.scope_key(doc_id, subfolder, active.active_dirs)
                source_label = scoped[0].title.partition(" — ")[0].strip() if doc_id else (subfolder or active.knowledge_dir)
                raw_key = x_api_key or (str(body.get("api_key")) if body.get("api_key") else None)
                t_cfg = workspace.build_tutor_config(provider, model, raw_key, 0.35).model_copy(update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language})
                return active, scoped, deck_path, prog_path, s_key, source_label, t_cfg

        active, scoped, deck_path, prog_path, s_key, source_label, t_cfg = await run_in_threadpool(_prep)
        messages = study_ai.build_flashcard_messages(scoped, count=count, style=style, language=active.language)
        tokens, err_detail = [], ""
        async for ev in stream_messages(messages, t_cfg, temperature=0.35, max_tokens=2048, request_id=x_request_id):
            if await request.is_disconnected():
                raise HTTPException(status_code=499, detail="Generation stopped by user.")
            if isinstance(ev, dict):
                if ev.get("type") == "error" and ev.get("detail"):
                    err_detail = str(ev["detail"])
                elif ev.get("type") == "token" and ev.get("delta"):
                    tokens.append(str(ev["delta"]))
        if err_detail and not tokens:
            raise HTTPException(status_code=502, detail=err_detail)
        cards = study_ai.parse_generated_cards("".join(tokens), scope=s_key, source_label=source_label, doc_id=doc_id or "", limit=count)
        if not cards:
            raise HTTPException(status_code=502, detail=err_detail or "Could not generate flashcards from the active model. Check that Ollama or your API key is ready and try again.")

        def _commit() -> dict[str, object]:
            with workspace.STATE_LOCK:
                latest_cfg = config()
                workspace.require_area(request, latest_cfg)
                if latest_cfg.knowledge_dir != active.knowledge_dir:
                    raise HTTPException(status_code=409, detail="Workspace changed while generating flashcards.")
                saved = study_ai.save_scope_cards(deck_path, s_key, cards)
                return {"area": active.knowledge_dir, "deck_mode": "ai", **study_cards.enrich_deck_with_progress(saved, study_cards.load_study_progress(prog_path))}

        return await run_in_threadpool(_commit)

    @router.post("/api/study/cards")
    async def add_custom_card(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        front, back = str(body.get("front") or "").strip()[:260], str(body.get("back") or "").strip()[:800]
        if not front or not back:
            raise HTTPException(status_code=422, detail="Enter both a question and an answer.")
        doc_id = str(body.get("doc_id") or "").strip() or None
        subfolder = str(body["subfolder"]).strip() if isinstance(body.get("subfolder"), str) else None

        def _save() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace first.")
                deck_path, prog_path = _study_paths(active.knowledge_dir)
                s_key = study_ai.scope_key(doc_id, subfolder, active.active_dirs)
                existing = study_ai.load_saved_decks(deck_path).get(s_key, []) or study_cards.extract_study_cards(chunks(), doc_id=doc_id, subfolder=subfolder, limit=20)
                card = {"id": study_ai._cid(s_key, front), "front": front, "back": back, "doc_id": doc_id or "", "source": str(body.get("source") or active.knowledge_dir), "tags": ["custom"], "origin": "custom"}
                saved = study_ai.save_scope_cards(deck_path, s_key, [card, *[c for c in existing if c.get("id") != card["id"]]])
                return {"area": active.knowledge_dir, "deck_mode": "ai", **study_cards.enrich_deck_with_progress(saved, study_cards.load_study_progress(prog_path))}

        return await run_in_threadpool(_save)

    @router.delete("/api/study/cards/{card_id}")
    def delete_study_card(card_id: str, request: Request, doc_id: str | None = None, subfolder: str | None = None) -> dict[str, object]:
        with workspace.STATE_LOCK:
            active = config()
            workspace.require_area(request, active)
            if not active.active_dirs:
                raise HTTPException(status_code=400, detail="Create or link a workspace first.")
            deck_path, prog_path = _study_paths(active.knowledge_dir)
            s_key = study_ai.scope_key(doc_id, subfolder, active.active_dirs)
            saved = study_ai.save_scope_cards(deck_path, s_key, [c for c in study_ai.load_saved_decks(deck_path).get(s_key, []) if str(c.get("id")) != card_id])
            return {"area": active.knowledge_dir, "deck_mode": "ai" if saved else "quick", **study_cards.enrich_deck_with_progress(saved, study_cards.load_study_progress(prog_path))}

    @router.post("/api/study/review")
    async def submit_study_review(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        card_id, raw_rating = str(body.get("card_id") or "").strip()[:32], str(body.get("rating") or "").strip().lower()
        if not card_id or raw_rating not in {"hard", "good", "easy"}:
            raise HTTPException(status_code=422, detail="Provide card_id and rating (hard, good, or easy)")
        rating: study_cards.StudyRating = "hard" if raw_rating == "hard" else ("good" if raw_rating == "good" else "easy")

        def _record() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace first.")
                _, prog_path = _study_paths(active.knowledge_dir)
                return {"review": study_cards.record_card_review(prog_path, card_id, rating)}

        return await run_in_threadpool(_record)

    return router
