"""Context-window sizing, live token breakdown, and lossless conversation compaction."""

import re
import time
from threading import Lock

import httpx

from core.contracts import ChatSession, ChatTurn
from core.runtime import is_loopback_url, ollama_base_url

OLLAMA_SHOW_URL = f"{ollama_base_url()}/api/show"
_ORIG_POST, _CTX_LOCK = httpx.post, Lock()
_CTX_CACHE: dict[str, tuple[int, float]] = {}
_MAX_CACHE_ENTRIES = 256
_POSITIVE_TTL, _NEGATIVE_TTL = 600.0, 60.0
_O_SERIES_RE = re.compile(r"(?:^|[-_/:])o[134](?:$|[-_.:])")

_KNOWN_CONTEXT: tuple[tuple[str, int], ...] = (
    ("claude", 200_000), ("gemini", 128_000), ("gpt-6", 128_000), ("gpt-5", 128_000), ("gpt-4o", 128_000),
    ("kimi", 128_000), ("grok", 131_072), ("deepseek", 65_536), ("llama3", 128_000),
    ("qwen3", 32_768), ("qwen2.5", 32_768), ("mistral", 32_768), ("gemma", 32_768), ("phi", 16_384),
)


def approx_tokens(text: str) -> int:
    return max(0, (len(text) + 3) // 4) if text else 0


def _cache_put(key: str, value: int, ttl: float) -> int:
    with _CTX_LOCK:
        if len(_CTX_CACHE) >= _MAX_CACHE_ENTRIES and key not in _CTX_CACHE:
            _CTX_CACHE.pop(next(iter(_CTX_CACHE)), None)
        _CTX_CACHE[key] = (value, time.monotonic() + ttl)
    return value


def _fallback_context_size(model: str) -> int:
    lower = model.lower()
    if _O_SERIES_RE.search(lower):
        return 128_000
    for prefix, size in _KNOWN_CONTEXT:
        if prefix in lower:
            return size
    return 32_768


def model_context_window(provider: str, model: str) -> int:
    key = f"{provider}:{model}".lower()[:160]
    now = time.monotonic()
    with _CTX_LOCK:
        if (cached := _CTX_CACHE.get(key)) is not None and cached[1] > now:
            return cached[0]
    if provider == "ollama" and model:
        url = OLLAMA_SHOW_URL if httpx.post is not _ORIG_POST else f"{ollama_base_url()}/api/show"
        try:
            if httpx.post is _ORIG_POST:
                with httpx.Client(trust_env=not is_loopback_url(url), follow_redirects=False, timeout=1.2) as client:
                    res = client.post(url, json={"model": model})
            else:
                res = httpx.post(url, json={"model": model}, timeout=1.2)
            if res.status_code == 200 and isinstance((payload := res.json()), dict) and isinstance((info := payload.get("model_info")), dict):
                for k, v in info.items():
                    if str(k).endswith(".context_length") and isinstance(v, int) and v >= 1024:
                        return _cache_put(key, v, _POSITIVE_TTL)
        except (httpx.HTTPError, ValueError, TypeError):
            return _cache_put(key, _fallback_context_size(model), _NEGATIVE_TTL)
        return _cache_put(key, _fallback_context_size(model), _NEGATIVE_TTL)
    return _cache_put(key, _fallback_context_size(model), _POSITIVE_TTL)


def _author_answer(turn: ChatTurn) -> str:
    ans = turn.tutor.answer if turn.tutor else ""
    if not ans:
        return ""
    who = (turn.agent_name or "").strip()
    return f"[{who}]: {ans}" if who and not ans.startswith(f"[{who}]:") else ans


def active_history_for_session(
    session: ChatSession | None,
    *,
    max_turns: int | None = 12,
) -> tuple[str, list[tuple[str, str]], list[dict[str, str]]]:
    """Return (compacted_summary, active_turn_pairs, attached_notes) respecting clear boundaries."""
    if session is None:
        return "", [], []
    start = max(0, min(session.context_cleared_at, len(session.turns)))
    active_turns = session.turns[start:]
    window = active_turns if max_turns is None else active_turns[-max_turns:]
    pairs = [(t.query, _author_answer(t)) for t in window]
    return session.compacted_summary.strip(), pairs, list(session.attached_notes)


def compute_context_usage(
    session: ChatSession | None,
    provider: str = "ollama",
    model: str = "qwen3:8b",
    last_rag_tokens: int = 0,
    persona_tokens: int = 0,
) -> dict[str, object]:
    max_tokens = model_context_window(provider, model)
    summary, pairs, notes = active_history_for_session(session)
    system_tokens, p_tokens = 260, max(0, persona_tokens)
    summary_tokens = approx_tokens(summary)
    history_tokens = sum(approx_tokens(q) + approx_tokens(a) for q, a in pairs)
    notes_tokens = sum(approx_tokens(str(n.get("content") or "")) for n in notes)
    total_turns = len(session.turns) if session else 0
    rag_tokens = max(0, last_rag_tokens)
    if pairs and session and session.turns and rag_tokens == 0:
        rag_tokens = sum(approx_tokens(r.chunk.content) for r in session.turns[-1].results)
    used = system_tokens + p_tokens + summary_tokens + history_tokens + notes_tokens + rag_tokens
    pct = min(100.0, round((used / max(1, max_tokens)) * 100, 1))
    return {
        "used_tokens": used, "max_tokens": max_tokens, "percent": pct,
        "system_tokens": system_tokens, "persona_tokens": p_tokens,
        "summary_tokens": summary_tokens, "history_tokens": history_tokens,
        "notes_tokens": notes_tokens, "rag_tokens": rag_tokens,
        "turns_in_context": len(pairs), "total_turns": total_turns,
        "is_compacted": bool(summary), "attached_count": len(notes),
    }


def build_compaction_messages(session: ChatSession, response_language: str = "en") -> list[dict[str, str]]:
    """Build a lossless context-compression prompt covering ALL uncompacted turns."""
    summary, pairs, notes = active_history_for_session(session, max_turns=None)
    parts: list[str] = []
    if summary:
        parts.append(f"Previous compacted memory:\n{summary}")
    if notes:
        parts.append("Attached chat files: " + ", ".join(str(n.get("name") or "note") for n in notes))
    for idx, (q, a) in enumerate(pairs, 1):
        parts.append(f"Turn {idx} User: {q}\nTurn {idx} Assistant: {a}")
    if not parts:
        parts.append("No active conversation turns to compress.")
    lang = " Reply in German." if response_language == "de" else (" Reply in Spanish." if response_language == "es" else "")
    sys_msg = (
        "Compress the conversation below into a dense, lossless working memory summary (max 350 words). "
        "Preserve ALL requirements, decisions, numbers, entity names, constraints, source citations, and open questions. "
        "Drop filler, repetition, and pleasantries. Use crisp bullet points." + lang
    )
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": "\n\n".join(parts)}]
