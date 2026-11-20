"""Hybrid BM25 + dense cosine + RRF search service."""

import math
import re
from collections import Counter

from core.contracts import KnowledgeChunk, SearchQuery, SearchResult
from core.scope import matches_scope

_TOKEN_RE = re.compile(r"\w+")
_STOPWORDS = frozenset([
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "did", "do", "does", "for", "from", "had", "has", "have", "how", "i", "in", "is", "it", "its", "me", "my",
    "of", "on", "or", "our", "should", "that", "the", "their", "them", "there", "these", "they", "this", "to", "was", "we", "were", "what", "when", "where", "which", "who", "why", "will", "with", "would", "you", "your",
    "aber", "als", "am", "auch", "auf", "aus", "bei", "bin", "bis", "das", "dem", "den", "der", "des", "die", "ein", "eine", "einem", "einen", "einer", "es", "fuer", "für", "hat", "ich", "im", "ist", "mit", "nach", "nicht", "oder", "sich", "sie", "sind", "und", "uns", "vom", "von", "war", "wie", "wir", "zu", "zum", "zur",
])
_BM25_K1 = 1.5
_BM25_B = 0.75


def tokenize(text: str) -> list[str]:
    """Extract lowercase word tokens while stripping punctuation and preserving identifiers."""
    return _TOKEN_RE.findall(text.casefold())


def query_terms(query: str) -> list[str]:
    """Extract deduplicated query terms, filtering stopwords when meaningful terms exist."""
    raw = list(dict.fromkeys(tokenize(query)))
    filtered = [term for term in raw if term not in _STOPWORDS]
    return filtered or raw


def _weighted_term_counts(chunk: KnowledgeChunk) -> tuple[dict[str, float], float]:
    counts: dict[str, float] = {}
    title_toks = tokenize(chunk.title)
    tag_toks = tokenize(" ".join(chunk.tags))
    body_toks = tokenize(chunk.content)
    for token, freq in Counter(title_toks).items():
        counts[token] = counts.get(token, 0.0) + freq * 3.0
    for token, freq in Counter(tag_toks).items():
        counts[token] = counts.get(token, 0.0) + freq * 2.0
    for token, freq in Counter(body_toks).items():
        counts[token] = counts.get(token, 0.0) + float(freq)
    doc_len = float(len(title_toks) * 3 + len(tag_toks) * 2 + len(body_toks)) or 1.0
    return counts, doc_len


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity; return 0.0 for mismatched or zero vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


def keyword_score(query: str, chunk: KnowledgeChunk) -> float:
    """Compute a punctuation-safe, field-weighted saturated lexical score for one chunk."""
    terms = query_terms(query)
    if not terms:
        return 0.0
    counts, _ = _weighted_term_counts(chunk)
    score = 0.0
    for term in terms:
        tf = counts.get(term, 0.0)
        if tf > 0.0:
            score += (tf * (_BM25_K1 + 1.0)) / (tf + _BM25_K1)
    return score


def _bm25_scores(query: str, chunks: list[KnowledgeChunk]) -> dict[str, float]:
    terms = query_terms(query)
    if not terms or not chunks:
        return {c.id: 0.0 for c in chunks}
    parsed = [(c.id, *_weighted_term_counts(c)) for c in chunks]
    avgdl = sum(dl for _, _, dl in parsed) / len(parsed)
    n_docs = len(parsed)
    df = {term: sum(1 for _, counts, _ in parsed if term in counts) for term in terms}
    idfs = {term: 1.0 + math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0) for term, freq in df.items() if freq > 0}
    scores: dict[str, float] = {}
    for cid, counts, dl in parsed:
        denom_scale = _BM25_K1 * (1.0 - _BM25_B + _BM25_B * (dl / avgdl))
        total = 0.0
        for term, idf in idfs.items():
            tf = counts.get(term, 0.0)
            if tf > 0.0:
                total += idf * ((tf * (_BM25_K1 + 1.0)) / (tf + denom_scale))
        scores[cid] = total
    return scores


def _lexical_rank(query: str, chunks: list[KnowledgeChunk], top_k: int) -> list[SearchResult]:
    scores = _bm25_scores(query, chunks)
    scored = [SearchResult(chunk=c, score=scores[c.id]) for c in chunks if scores[c.id] > 0.0]
    scored.sort(key=lambda result: result.score, reverse=True)
    return scored[:top_k]


def hybrid_search(
    search_query: SearchQuery,
    chunks: list[KnowledgeChunk],
    query_embedding: list[float] | None = None,
) -> list[SearchResult]:
    """Run BM25 lexical, dense cosine vector, or RRF hybrid search and return up to ``top_k``."""
    candidates = [
        chunk
        for chunk in chunks
        if matches_scope(chunk, search_query.doc_id, search_query.subfolder)
        and (not search_query.tag_filter or search_query.tag_filter.lower() in {tag.lower() for tag in chunk.tags})
    ]
    query = search_query.query.strip()
    if not query:
        if not search_query.tag_filter and search_query.doc_id is None and search_query.subfolder is None:
            return []
        return [SearchResult(chunk=chunk, score=1.0) for chunk in candidates[: search_query.top_k]]

    mode = search_query.retrieval_mode
    has_vectors = bool(query_embedding) and any(bool(chunk.embedding) for chunk in candidates)
    if mode == "lexical" or not has_vectors:
        return _lexical_rank(query, candidates, search_query.top_k)

    q_vec = query_embedding or []
    if mode == "vector":
        vec_scored = [
            SearchResult(chunk=chunk, score=sim)
            for chunk in candidates
            if chunk.embedding and (sim := cosine_similarity(q_vec, chunk.embedding)) > 0.0
        ]
        vec_scored.sort(key=lambda result: result.score, reverse=True)
        return vec_scored[: search_query.top_k] or _lexical_rank(query, candidates, search_query.top_k)

    lex_map = _bm25_scores(query, candidates)
    vec_map = {c.id: cosine_similarity(q_vec, c.embedding) if c.embedding else 0.0 for c in candidates}
    active = [c for c in candidates if lex_map[c.id] > 0.0 or vec_map[c.id] > 0.0]
    if not active:
        return []
    lex_ranks = {c.id: idx + 1 for idx, c in enumerate(sorted(active, key=lambda c: lex_map[c.id], reverse=True))}
    vec_ranks = {c.id: idx + 1 for idx, c in enumerate(sorted(active, key=lambda c: vec_map[c.id], reverse=True))}

    fused: list[tuple[float, float, SearchResult]] = []
    for chunk in active:
        rrf = (1.0 / (search_query.rrf_k + lex_ranks[chunk.id])) + (1.0 / (search_query.rrf_k + vec_ranks[chunk.id]))
        total = lex_map[chunk.id] + vec_map[chunk.id] + rrf
        fused.append((rrf, total, SearchResult(chunk=chunk, score=total)))
    fused.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [item[2] for item in fused[: search_query.top_k]]
