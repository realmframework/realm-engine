"""Retrieval X-Ray: exact BM25, Cosine Vector, and RRF rank/score decomposition with pin/mute overrides."""

import math
import re
from collections import Counter

from core.contracts import KnowledgeChunk
from core.scope import matches_scope

_TOKEN_RE = re.compile(r"\w+")
_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "did", "do", "does", "for", "from", "had", "has", "have", "how", "i", "in", "is", "it", "its", "me", "my",
    "of", "on", "or", "our", "should", "that", "the", "their", "them", "there", "these", "they", "this", "to", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "would", "you", "your",
    "aber", "als", "am", "auch", "auf", "aus", "bei", "bin", "bis", "das", "dem", "den", "der", "des", "die", "ein", "eine", "einem", "einen", "einer", "es", "fuer", "für", "hat", "ich", "im", "ist", "mit", "nach", "nicht", "oder", "sich", "sie", "sind", "und", "uns", "vom", "von", "war", "wie", "wir", "zu", "zum", "zur",
    "al", "como", "con", "de", "del", "el", "en", "la", "las", "lo", "los", "para", "por", "que", "se", "su", "un", "una", "y",
})


def _terms(query: str) -> list[str]:
    toks = list(dict.fromkeys(_TOKEN_RE.findall(query.casefold())))
    filtered = [t for t in toks if t not in _STOPWORDS]
    return filtered or toks


def _weighted_counts(chunk: KnowledgeChunk) -> tuple[dict[str, float], float]:
    counts: dict[str, float] = {}
    t_toks = _TOKEN_RE.findall(chunk.title.casefold())
    g_toks = _TOKEN_RE.findall(" ".join(chunk.tags).casefold())
    b_toks = _TOKEN_RE.findall(chunk.content.casefold())
    for tok, freq in Counter(t_toks).items():
        counts[tok] = counts.get(tok, 0.0) + freq * 3.0
    for tok, freq in Counter(g_toks).items():
        counts[tok] = counts.get(tok, 0.0) + freq * 2.0
    for tok, freq in Counter(b_toks).items():
        counts[tok] = counts.get(tok, 0.0) + float(freq)
    return counts, float(len(t_toks) * 3 + len(g_toks) * 2 + len(b_toks)) or 1.0


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b))
    if not (math.isfinite(dot) and math.isfinite(na) and math.isfinite(nb)) or not na or not nb:
        return 0.0
    sim = dot / (na * nb)
    return sim if math.isfinite(sim) else 0.0


def build_retrieval_xray(
    query_text: str,
    chunks: list[KnowledgeChunk],
    top_k: int = 5,
    rrf_k: int = 60,
    retrieval_mode: str = "hybrid",
    query_embedding: list[float] | None = None,
    doc_id: str | None = None,
    subfolder: str | None = None,
    muted_doc_ids: list[str] | None = None,
    pinned_doc_ids: list[str] | None = None,
) -> list[dict[str, object]]:
    """Compute transparent BM25, Vector Cosine, and RRF rank breakdown per retrieved passage."""
    muted = {m.strip() for m in (muted_doc_ids or []) if m.strip()}
    pinned = {p.strip() for p in (pinned_doc_ids or []) if p.strip()}
    scoped = [c for c in chunks if matches_scope(c, doc_id, subfolder) and c.doc_id not in muted]
    if not scoped:
        return []

    terms = _terms(query_text)
    parsed = [(c, *_weighted_counts(c)) for c in scoped]
    avgdl = sum(dl for _, _, dl in parsed) / len(parsed)
    n_docs = len(parsed)
    df = {term: sum(1 for _, counts, _ in parsed if term in counts) for term in terms}
    idfs = {term: 1.0 + math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0) for term, freq in df.items() if freq > 0}

    bm25_map: dict[str, float] = {}
    vec_map: dict[str, float] = {}
    for c, counts, dl in parsed:
        denom = 1.5 * (0.25 + 0.75 * (dl / avgdl))
        bm25_map[c.id] = sum(idf * ((counts[t] * 2.5) / (counts[t] + denom)) for t, idf in idfs.items() if counts.get(t, 0.0) > 0.0)
        vec_map[c.id] = _cosine(query_embedding, c.embedding) if (query_embedding and c.embedding) else 0.0

    bm25_sorted = [cid for cid, sc in sorted(bm25_map.items(), key=lambda p: (-p[1], p[0])) if sc > 0.0]
    vec_sorted = [cid for cid, sc in sorted(vec_map.items(), key=lambda p: (-p[1], p[0])) if sc > 0.0]
    bm25_rank = {cid: idx + 1 for idx, cid in enumerate(bm25_sorted)}
    vec_rank = {cid: idx + 1 for idx, cid in enumerate(vec_sorted)}

    scored_rows: list[tuple[bool, float, str, dict[str, object]]] = []
    for c in scoped:
        br, vr = bm25_rank.get(c.id), vec_rank.get(c.id)
        is_pin = c.doc_id in pinned
        if retrieval_mode == "lexical":
            fused = bm25_map[c.id]
        elif retrieval_mode == "vector":
            fused = vec_map[c.id]
        else:
            fused = (1.0 / (rrf_k + br) if br else 0.0) + (1.0 / (rrf_k + vr) if vr else 0.0)
        if fused <= 0.0 and not is_pin:
            continue
        scored_rows.append((
            not is_pin, -fused, c.id,
            {
                "chunk_id": c.id, "doc_id": c.doc_id, "title": c.title, "area": c.area,
                "bm25_score": round(bm25_map[c.id], 3), "bm25_rank": br,
                "vector_score": round(vec_map[c.id], 3), "vector_rank": vr,
                "rrf_score": round(fused, 4), "pinned": is_pin,
                "snippet": c.content[:180].strip(),
            },
        ))
    scored_rows.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in scored_rows[: max(1, min(15, top_k))]]
