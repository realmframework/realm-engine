"""Context-window sizing, live token breakdown, and lossless conversation compaction."""

import httpx

from core.contracts import ChatSession

OLLAMA_SHOW_URL = "http://127.0.0.1:11434/api/show"
_CTX_CACHE: dict[str, int] = {}

_KNOWN_CONTEXT: tuple[tuple[str, int], ...] = (
    ("claude", 200_000),
    ("gemini", 128_000),
    ("gpt-6", 128_000),
    ("gpt-5", 128_000),
    ("gpt-4o", 128_000),
    ("o1", 128_000),
    ("o3", 128_000),
    ("o4", 128_000),
    ("kimi", 128_000),
    ("grok", 131_072),
    ("deepseek", 65_536),
    ("llama3", 128_000),
    ("qwen3", 32_768),
    ("qwen2.5", 32_768),
    ("mistral", 32_768),
    ("gemma", 32_768),
    ("phi", 16_384),
)


def approx_tokens(text: str) -> int:
    return max(0, (len(text) + 3) // 4) if text else 0


def model_context_window(provider: str, model: str) -> int:
    key = f"{provider}:{model}".lower()
    if key in _CTX_CACHE:
        return _CTX_CACHE[key]
    if provider == "ollama" and model:
        try:
            res = httpx.post(OLLAMA_SHOW_URL, json={"model": model}, timeout=1.2)
            if res.status_code == 200:
                info = res.json().get("model_info")
                if isinstance(info, dict):
                    for k, v in info.items():
                        if str(k).endswith(".context_length") and isinstance(v, int) and v >= 1024:
                            _CTX_CACHE[key] = v
                            return v
        except (httpx.HTTPError, ValueError, TypeError):
            pass
    lower = model.lower()
    for prefix, size in _KNOWN_CONTEXT:
        if prefix in lower:
            _CTX_CACHE[key] = size
            return size
    return 32_768


def active_history_for_session(session: ChatSession | None) -> tuple[str, list[tuple[str, str]], list[dict[str, str]]]:
    """Return (compacted_summary, active_turn_pairs, attached_notes) respecting clear boundaries."""
    if session is None:
        return "", [], []
    start = max(0, min(session.context_cleared_at, len(session.turns)))
    active_turns = session.turns[start:]
    pairs = [(t.query, t.tutor.answer if t.tutor else "") for t in active_turns[-12:]]
    return session.compacted_summary.strip(), pairs, list(session.attached_notes)


def compute_context_usage(
    session: ChatSession | None,
    provider: str = "ollama",
    model: str = "qwen3:8b",
    last_rag_tokens: int = 0,
) -> dict[str, object]:
    max_tokens = model_context_window(provider, model)
    summary, pairs, notes = active_history_for_session(session)
    system_tokens = 260
    summary_tokens = approx_tokens(summary)
    history_tokens = sum(approx_tokens(q) + approx_tokens(a) for q, a in pairs)
    notes_tokens = sum(approx_tokens(str(n.get("content") or "")) for n in notes)
    total_turns = len(session.turns) if session else 0
    active_count = max(0, total_turns - (session.context_cleared_at if session else 0))
    rag_tokens = max(0, last_rag_tokens)
    if active_count > 0 and session and session.turns and rag_tokens == 0:
        last_turn = session.turns[-1]
        rag_tokens = sum(approx_tokens(r.chunk.content) for r in last_turn.results)
    used = system_tokens + summary_tokens + history_tokens + notes_tokens + rag_tokens
    pct = min(100.0, round((used / max(1, max_tokens)) * 100, 1))
    return {
        "used_tokens": used,
        "max_tokens": max_tokens,
        "percent": pct,
        "system_tokens": system_tokens,
        "summary_tokens": summary_tokens,
        "history_tokens": history_tokens,
        "notes_tokens": notes_tokens,
        "rag_tokens": rag_tokens,
        "turns_in_context": active_count,
        "total_turns": total_turns,
        "is_compacted": bool(summary),
        "attached_count": len(notes),
    }


def build_compaction_messages(session: ChatSession, response_language: str = "en") -> list[dict[str, str]]:
    """Build a lossless context-compression prompt summarizing earlier turns."""
    summary, pairs, notes = active_history_for_session(session)
    parts: list[str] = []
    if summary:
        parts.append(f"Previous compacted memory:\n{summary}")
    if notes:
        parts.append("Attached chat files: " + ", ".join(str(n.get("name") or "note") for n in notes))
    for idx, (q, a) in enumerate(pairs, 1):
        parts.append(f"Turn {idx} User: {q}\nTurn {idx} Assistant: {a}")
    lang = " Reply in German." if response_language == "de" else (" Reply in Spanish." if response_language == "es" else "")
    sys_msg = (
        "Compress the conversation below into a dense, lossless working memory summary (max 350 words). "
        "Preserve ALL requirements, decisions, numbers, entity names, constraints, source citations, and open questions. "
        "Drop filler, repetition, and pleasantries. Use crisp bullet points." + lang
    )
    return [{"role": "system", "content": sys_msg}, {"role": "user", "content": "\n\n".join(parts)}]
