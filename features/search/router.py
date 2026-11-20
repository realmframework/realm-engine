"""Fast Query Intent Decision Router for adaptive RAG retrieval parameters."""

import re

_CODE_TOKEN_RE = re.compile(
    r"(?:[a-zA-Z0-9]+_[a-zA-Z0-9_]+|--[a-zA-Z0-9-]+|[a-zA-Z0-9_-]+\.(?:py|md|json|ts|js|sh|yaml|toml)\b|/[a-zA-Z0-9_.-]+|`[^`]+`)"
)
_DEEP_KEYWORDS = {
    "compare",
    "comparison",
    "difference",
    "differences",
    "architecture",
    "versus",
    "vs",
    "why",
    "tradeoff",
    "tradeoffs",
}
_DEEP_PHRASES = ("how does", "how do", "walk through", "in depth", "end to end")
_FOLLOWUP_PRONOUNS = {"it", "its", "that", "this", "they", "them", "those", "these", "their"}
_STOPWORDS = {
    "what", "how", "why", "when", "where", "who", "which", "is", "are", "was", "were",
    "do", "does", "did", "can", "could", "should", "would", "the", "a", "an", "in",
    "on", "at", "to", "for", "of", "with", "by", "from", "and", "or", "about",
}


def _extract_key_terms(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_.-]+", text)
    return [w for w in words if len(w) >= 2 and w.lower() not in _STOPWORDS][:6]


def route_query_intent(
    query: str,
    history: list[tuple[str, str]] | None = None,
    top_k: int = 5,
    retrieval_mode: str = "hybrid",
    rrf_k: int = 60,
) -> dict[str, object]:
    """Classify query intent and return routed retrieval parameters and decision badge label."""
    cleaned = query.strip()
    words = re.findall(r"[A-Za-z0-9_'-]+", cleaned)
    lower_words = [w.lower() for w in words]
    lower_q = cleaned.lower()
    is_auto = top_k == 5 and retrieval_mode == "hybrid" and rrf_k == 60

    if history and any(p in lower_words for p in _FOLLOWUP_PRONOUNS) and len(words) <= 12:
        prev_query = history[-1][0].strip()
        prev_terms = " ".join(_extract_key_terms(prev_query)) or prev_query
        routed_q = f"{prev_terms} {cleaned}".strip() if prev_terms.lower() not in lower_q else cleaned
        return {
            "intent": "contextual_followup",
            "label": "Auto-Router: Contextual Follow-up",
            "routed_query": routed_q,
            "retrieval_mode": retrieval_mode,
            "top_k": top_k,
            "rrf_k": rrf_k,
        }

    is_deep = (
        any(k in lower_words for k in _DEEP_KEYWORDS)
        or any(p in lower_q for p in _DEEP_PHRASES)
        or len(words) > 10
    )
    has_code = bool(_CODE_TOKEN_RE.search(cleaned))

    if has_code or (0 < len(words) <= 3 and not is_deep):
        return {
            "intent": "exact_lookup",
            "label": "Auto-Router: Exact Lookup",
            "routed_query": cleaned,
            "retrieval_mode": "hybrid" if is_auto else retrieval_mode,
            "top_k": top_k,
            "rrf_k": 30 if is_auto else rrf_k,
        }

    if is_deep:
        return {
            "intent": "deep_synthesis",
            "label": "Auto-Router: Deep Synthesis",
            "routed_query": cleaned,
            "retrieval_mode": "hybrid" if is_auto else retrieval_mode,
            "top_k": max(top_k, 7) if is_auto else top_k,
            "rrf_k": rrf_k,
        }

    return {
        "intent": "exact_lookup",
        "label": "Auto-Router: Exact Lookup",
        "routed_query": cleaned,
        "retrieval_mode": retrieval_mode,
        "top_k": top_k,
        "rrf_k": 30 if is_auto else rrf_k,
    }
