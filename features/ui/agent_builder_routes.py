"""Interactive conversational Agent Builder endpoint (interviews user & drafts persona.md)."""

import json
import re
from collections.abc import AsyncIterator, Callable

from fastapi import APIRouter, Header, HTTPException, Request

from core.contracts import WorkspaceConfig
from core.format_presets import BUILTIN_FORMATS
from core.work_contracts import AgentDraft
from features.ui import route_helpers, workspace
from features.ui.privacy import require_local

StreamMessagesFn = Callable[..., AsyncIterator[dict[str, object]]]
_VALID_PALETTES = ("realm", "lisbeth", "salander", "wasp", "plague", "blomkvist", "millennium", "erika", "harriet", "milton", "dragon", "hacker", "stieg", "annika", "palmgren")
_VALID_FORMATS = {f.id for f in BUILTIN_FORMATS}
_DRAFT_RE = re.compile(r"<agent_draft>\s*(\{[\s\S]*?\})\s*</agent_draft>", re.IGNORECASE)
_LANG_MAP = {"de": "German", "es": "Spanish", "en": "English"}


def _architect_system(language: str, force_draft: bool) -> str:
    lang_name = _LANG_MAP.get(language, "English")
    palettes = ", ".join(_VALID_PALETTES)
    formats = ", ".join(sorted(_VALID_FORMATS))
    phase_rule = (
        "The user asked to draft the agent NOW. Briefly summarize the proposed agent in 2 sentences and ALWAYS include the complete <agent_draft>{...}</agent_draft> JSON block."
        if force_draft
        else (
            "Interview the user warmly in 2–4 short turns to design their ideal personal AI agent. "
            "Ask only 1–2 crisp, plain-language questions per reply (about their work goals, tone/style, concrete habits, or boundaries). "
            "As soon as you have enough detail (typically after 2–3 user messages, or immediately if they already described role + style), "
            "present a concise summary AND include a complete <agent_draft>{...}</agent_draft> JSON block so they can preview and save with 1 click."
        )
    )
    return (
        f"You are the REALM Agent Architect. Always respond in {lang_name} unless the user writes in another language. "
        f"{phase_rule}\n\n"
        "When outputting a draft, wrap valid JSON strictly inside <agent_draft>...</agent_draft> with exact keys:\n"
        '{"name":"Short Name (max 30 chars)","role":"Clear Role","tagline":"1-sentence superpower",'
        f'"palette":"one of: {palettes}","default_format":"empty string or one of: {formats}",'
        '"temperature":0.25,"instructions":"## Analytical Lens\\n...\\n\\n## Signature Moves\\n- ...\\n\\n## Communication Style\\n...\\n\\n## Boundaries\\nNever ..."}'
    )


def _extract_draft(raw: str) -> tuple[str, AgentDraft | None]:
    match = _DRAFT_RE.search(raw)
    if not match:
        return raw.strip(), None
    visible = _DRAFT_RE.sub("", raw).strip()
    try:
        parsed = json.loads(match.group(1))
        if not isinstance(parsed, dict):
            return visible, None
        palette = str(parsed.get("palette") or "realm").strip().lower()
        fmt = str(parsed.get("default_format") or "").strip().lower()
        raw_temp = parsed.get("temperature", 0.25)
        temp = max(0.0, min(1.0, float(raw_temp) if isinstance(raw_temp, (int, float, str)) else 0.25))
        draft = AgentDraft(
            name=str(parsed.get("name") or "Custom Agent").strip()[:40] or "Custom Agent",
            role=str(parsed.get("role") or "Specialist").strip()[:64] or "Specialist",
            tagline=str(parsed.get("tagline") or "").strip()[:160],
            palette=palette if palette in _VALID_PALETTES else "realm",
            default_format=fmt if fmt in _VALID_FORMATS else "",
            temperature=round(temp, 2),
            instructions=str(parsed.get("instructions") or "").strip()[:3000],
        )
        return visible or f"Here is your draft for **{draft.name}** — review the preview below or ask me to adjust anything.", draft
    except (ValueError, TypeError):
        return visible or raw.strip(), None


def _fallback_draft(user_texts: list[str]) -> AgentDraft:
    combined = " ".join(user_texts).strip()
    words = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß0-9]+", combined) if len(w) > 3]
    short_topic = " ".join(words[:3]).title() if words else "Work Partner"
    return AgentDraft(
        name=short_topic[:24] or "Work Partner",
        role="Personal Specialist",
        tagline=(combined[:140] if combined else "Focused personal work assistant."),
        palette="harriet",
        default_format="",
        temperature=0.25,
        instructions=(
            f"## Analytical Lens\nFocus on helping with: {combined or 'structured work, clarity, and practical decisions'}.\n\n"
            "## Signature Moves\n- Structure answers clearly with concrete takeaways and next steps.\n- Flag missing information instead of guessing.\n\n"
            "## Communication Style\nWarm, clear, practical, and easy to scan.\n\n"
            "## Boundaries\nNever invent facts, figures, or quotes not supported by the user's notes."
        ),
    )


def build_router(get_config: Callable[[], WorkspaceConfig], stream_messages: StreamMessagesFn) -> APIRouter:
    router = APIRouter()

    @router.post("/api/agents/builder/chat")
    async def agent_builder_chat(request: Request, x_api_key: str | None = Header(default=None, alias="x-api-key")) -> dict[str, object]:
        body = await route_helpers.read_json_dict(request)
        raw_msgs = body.get("messages")
        if not isinstance(raw_msgs, list) or not raw_msgs:
            raise HTTPException(status_code=400, detail="Provide at least one conversation message")
        clean_msgs: list[dict[str, str]] = []
        for item in raw_msgs[-16:]:
            if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and str(item.get("content") or "").strip():
                clean_msgs.append({"role": str(item["role"]), "content": str(item["content"]).strip()[:4000]})
        if not clean_msgs:
            raise HTTPException(status_code=400, detail="Provide valid user or assistant messages")

        force_draft = bool(body.get("force_draft"))
        provider = str(body.get("provider") or "ollama").strip()
        model = str(body.get("model") or "").strip() or None
        api_key = x_api_key or (str(body.get("api_key")).strip() if body.get("api_key") else None)
        with workspace.STATE_LOCK:
            active = get_config()
            require_local(active, provider, model)
            t_cfg = workspace.build_tutor_config(provider, model, api_key, 0.35).model_copy(
                update={"daily_cloud_request_limit": active.daily_cloud_request_limit, "daily_budget_usd_limit": active.daily_budget_usd_limit, "response_language": active.language}
            )
            lang = active.language

        prompt_msgs = [{"role": "system", "content": _architect_system(lang, force_draft)}, *clean_msgs]
        if force_draft:
            prompt_msgs.append({"role": "user", "content": "Generate the complete <agent_draft> JSON now based on everything discussed."})

        emitted: list[str] = []
        stream_err = ""
        async for ev in stream_messages(prompt_msgs, t_cfg, temperature=0.35, max_tokens=1400):
            if ev.get("type") == "token" and ev.get("delta"):
                emitted.append(str(ev["delta"]))
            elif ev.get("type") == "error":
                stream_err = str(ev.get("detail") or "Could not reach AI provider")
                break

        raw_reply = "".join(emitted).strip()
        if not raw_reply:
            if force_draft:
                fb = _fallback_draft([m["content"] for m in clean_msgs if m["role"] == "user"])
                return {"reply": stream_err or "Drafted a starter agent from your notes below — you can refine or save it directly.", "draft": fb.model_dump(), "fallback": True}
            raise HTTPException(status_code=503, detail=stream_err or "Could not reach the configured AI model. Check Ollama or your API key.")

        reply_text, draft = _extract_draft(raw_reply)
        if force_draft and draft is None:
            draft = _fallback_draft([m["content"] for m in clean_msgs if m["role"] == "user"])
        return {"reply": reply_text, "draft": draft.model_dump() if draft else None, "fallback": False}

    return router
