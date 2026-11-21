"""Phase 6 routes: Offline Audio Briefing, Retrieval X-Ray, and SSRF-safe Web Clipper."""

import base64
import os
from collections.abc import Callable
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool

from core.audio_briefing import build_briefing_script, synthesize_briefing_audio
from core.contracts import KnowledgeChunk, WorkspaceConfig
from core.linked_vaults import is_linked_vault
from core.model_routing import ollama_slot
from core.retrieval_xray import build_retrieval_xray
from core.runtime import is_loopback_url, ollama_base_url
from core.web_clipper import clip_url_to_markdown
from features.ui import (
    audio_routes,
    folders,
    openai_local_routes,
    route_helpers,
    workspace,
)
from features.ui.guide_edit_routes import _safe_slug, _unique_md_path
from features.ui.privacy import require_local

_ORIG_HTTPX_POST = httpx.post
def _speak_local_phonon(text: str, voice: str, model: str = "phonon:latest") -> tuple[bytes, str] | None:
    payload = {"model": model, "input": text, "voice": audio_routes.strip_voice_label(voice)}
    url = f"{ollama_base_url()}/v1/audio/speech" if httpx.post is _ORIG_HTTPX_POST else audio_routes.OLLAMA_SPEECH_URL
    try:
        with ollama_slot("ollama", model):
            if httpx.post is _ORIG_HTTPX_POST:
                with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=25.0) as client:
                    res = client.post(url, json=payload)
            else:
                res = httpx.post(url, json=payload, timeout=25.0)
        if res.status_code == 200 and res.content:
            return res.content, res.headers.get("content-type", "audio/wav").split(";")[0]
    except httpx.HTTPError:
        pass
    return None
def build_router(config: Callable[[], WorkspaceConfig], chunks: Callable[[], list[KnowledgeChunk]], reindex: Callable[[Path], list[KnowledgeChunk]] | None = None) -> APIRouter:
    router = APIRouter()
    @router.post("/api/audio/briefing")
    async def generate_audio_briefing(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, required=False, non_dict_status=422)
        mode = "duo" if str(body.get("mode") or "solo") == "duo" else "solo"
        host_a, host_b = str(body.get("host_a") or "Saga")[:40], str(body.get("host_b") or "Blomkvist")[:40]
        voice_a, voice_b, tts_model = str(body.get("voice_a") or "default"), str(body.get("voice_b") or "Easton"), str(body.get("model") or "phonon:latest")
        raw_ids = body.get("doc_ids")
        doc_ids = [str(d) for d in raw_ids] if isinstance(raw_ids, list) and raw_ids else None
        subfolder, skip_tts = str(body.get("subfolder") or "").strip() or None, bool(body.get("script_only")) or tts_model == "disabled"
        def _work() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not skip_tts:
                    require_local(active, "ollama", tts_model)
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace before generating a briefing.")
                script = build_briefing_script(chunks(), mode=mode, host_a=host_a, host_b=host_b, doc_ids=doc_ids, subfolder=subfolder, area_label=active.knowledge_dir.replace("_", " ").replace("-", " "))
            if not script:
                raise HTTPException(status_code=400, detail="No guides available in this scope to brief.")
            transcript = "\n\n".join(f"**{line['speaker']}:** {line['text']}" for line in script)
            audio_bytes, mime = (None, "") if skip_tts else synthesize_briefing_audio(script, lambda txt, v: _speak_local_phonon(txt, v, tts_model), voice_a=voice_a, voice_b=voice_b)
            return {"mode": mode, "script": script, "transcript": transcript, "synthesized": bool(audio_bytes), "audio_base64": base64.b64encode(audio_bytes).decode("ascii") if audio_bytes else None, "audio_mime": mime or "audio/wav", "notice": "" if audio_bytes else "Local Phonon TTS is offline — full briefing transcript is ready below."}
        return await run_in_threadpool(_work)

    @router.post("/api/search/xray")
    async def search_xray(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        if not (q := str(body.get("query") or "").strip()):
            return {"query": "", "rows": []}
        try:
            top_k = max(1, min(15, int(str(body.get("top_k") or 5))))
            rrf_k = max(1, min(120, int(str(body.get("rrf_k") or 60))))
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="top_k and rrf_k must be integers") from exc
        mode, raw_muted, raw_pinned = str(body.get("retrieval_mode") or "hybrid"), body.get("muted_doc_ids"), body.get("pinned_doc_ids")
        muted = [str(m) for m in raw_muted] if isinstance(raw_muted, list) else []
        pinned = [str(p) for p in raw_pinned] if isinstance(raw_pinned, list) else []

        def _scan() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if not active.active_dirs:
                    return {"query": q, "rows": []}
                rows = build_retrieval_xray(q, list(chunks()), top_k=top_k, rrf_k=rrf_k, retrieval_mode=mode, doc_id=str(body.get("doc_id") or "") or None, subfolder=str(body.get("subfolder") or "") or None, muted_doc_ids=muted, pinned_doc_ids=pinned)
            return {"query": q, "retrieval_mode": mode, "rrf_k": rrf_k, "rows": rows}

        return await run_in_threadpool(_scan)

    @router.post("/api/guides/clip-url")
    async def clip_web_url(request: Request) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request, non_dict_status=422)
        if not (url := str(body.get("url") or "").strip()):
            raise HTTPException(status_code=422, detail="Provide a valid http(s) URL to clip")
        subfolder, req_area = str(body.get("subfolder") or "").strip(), str(body.get("area") or "").strip()

        def _precheck() -> str:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if active.strict_local_only:
                    raise HTTPException(status_code=403, detail="Strict Local-Only Lock is ON — allow external access in Privacy to clip web URLs.")
                if not active.active_dirs:
                    raise HTTPException(status_code=400, detail="Create or link a workspace before clipping web pages.")
                area = req_area or active.knowledge_dir
                if area not in active.active_dirs:
                    raise HTTPException(status_code=400, detail="Save to one of the active workspaces")
                if is_linked_vault(area, workspace.REPO_ROOT):
                    raise HTTPException(status_code=403, detail="Linked folders are read-safe — clip web pages into a managed workspace instead.")
                return area

        area = await run_in_threadpool(_precheck)
        try:
            title, md = await run_in_threadpool(clip_url_to_markdown, url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=400, detail="Could not fetch the target URL safely") from exc

        def _commit() -> dict[str, object]:
            with workspace.STATE_LOCK:
                active = config()
                workspace.require_area(request, active)
                if area not in active.active_dirs or is_linked_vault(area, workspace.REPO_ROOT):
                    raise HTTPException(status_code=409, detail="Workspace changed while clipping this URL. Select it and try again.")
                target = workspace.resolve_safe_knowledge_dir(area, create=False)
                out_path = _unique_md_path(folders.resolve_subfolder(target, subfolder, create=True), _safe_slug(title))
                if out_path.is_symlink():
                    raise HTTPException(status_code=400, detail="Cannot write clipped guide to a symbolic link")
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
                try:
                    with os.fdopen(os.open(out_path, flags, 0o644), "w", encoding="utf-8") as handle:
                        handle.write(md)
                except OSError as exc:
                    out_path.unlink(missing_ok=True)
                    raise HTTPException(status_code=500, detail="Could not save clipped guide") from exc
                updated_chunks = reindex(target) if reindex else chunks()
                rel_id = out_path.relative_to(target).with_suffix("").as_posix()
                return {**workspace.build_workspace_payload(active, updated_chunks), "doc_id": f"{area}::{rel_id}" if len(active.active_dirs) > 1 else rel_id, "title": title, "source_url": url}
        return await run_in_threadpool(_commit)
    router.include_router(openai_local_routes.build_router(config, chunks))
    return router
