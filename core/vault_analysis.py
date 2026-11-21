"""Deterministic local workspace analyzer for contradictions, near-duplicates, and orphan topics."""

import re
from collections import defaultdict

from core.contracts import KnowledgeChunk

_STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "your", "into", "have", "will", "about",
    "overview", "summary", "notes", "guide", "introduction", "conclusion", "sources", "section",
    "der", "die", "das", "und", "mit", "für", "von", "eine", "einer", "los", "las", "para", "con",
}
_CLAIM_RE = re.compile(
    r"(?im)(?:^|[.;][ \t]+)[ \t]*(?:[-*][ \t]*)?(?:\*\*)?([^\W\d_][\w /_-]{2,34})(?:\*\*)?[ \t]*:[ \t]*([^\n;]{1,80})"
)
_VAL_RE = re.compile(
    r"(?:[$€£][ \t]?\d[\d,.]*[ \t]*[kmb]?|\b\d+(?:[.,]\d+)?[ \t]*(?:%|(?:ms|s|gb|mb|tb|kb|days?|weeks?|months?|years?|usd|eur)\b)|\b(?:19|20)\d{2}\b)",
    re.IGNORECASE,
)


def _norm_words(text: str) -> set[str]:
    words = re.findall(r"[^\W_]{3,}", text.casefold())
    return {w for w in words if w not in _STOPWORDS}


def _extract_claims(text: str) -> list[tuple[str, str, str]]:
    found: list[tuple[str, str, str]] = []
    for match in _CLAIM_RE.finditer(text):
        key = re.sub(r"\s+", " ", match.group(1).strip().casefold())
        if len(key) < 3 or key in {"title", "tags", "created_at", "description", "url", "http", "https", "date"}:
            continue
        rhs = re.split(r"\.(?:\s|$)", match.group(2).strip(), maxsplit=1)[0].strip()
        val_match = _VAL_RE.search(rhs)
        if val_match:
            val = re.sub(r"\s+", " ", val_match.group(0).strip().casefold())
            found.append((key, val, f"{match.group(1).strip()}: {rhs[:80]}"))
    return found


def _group_guides(chunks: list[KnowledgeChunk]) -> list[dict[str, object]]:
    by_doc: dict[str, dict[str, object]] = {}
    for chunk in chunks:
        doc_id = chunk.doc_id or chunk.file_path
        title = chunk.title.split(" — ", 1)[0].strip() or doc_id
        entry = by_doc.setdefault(doc_id, {"doc_id": doc_id, "title": title, "parts": [], "tags": set(), "headings": []})
        if isinstance((parts := entry["parts"]), list):
            parts.append(chunk.content)
        if isinstance((tags := entry["tags"]), set):
            tags.update(t.strip().casefold() for t in chunk.tags if t.strip())
        sec = chunk.title.split(" — ", 1)[1].strip() if " — " in chunk.title else ""
        if sec and isinstance((headings := entry["headings"]), list):
            headings.append(sec)
    guides: list[dict[str, object]] = []
    for item in by_doc.values():
        parts = item["parts"]
        body = "\n\n".join(str(p) for p in parts) if isinstance(parts, list) else ""
        guides.append({
            "doc_id": str(item["doc_id"]), "title": str(item["title"]), "body": body,
            "words": _norm_words(f"{item['title']} {body}"),
            "tags": sorted(str(t) for t in item["tags"]) if isinstance(item["tags"], set) else [],
            "headings": list(item["headings"]) if isinstance(item["headings"], list) else [],
        })
    return guides


def analyze_workspace_gaps(chunks: list[KnowledgeChunk]) -> dict[str, object]:
    """Find cross-guide numeric/date conflicts, near-duplicate guides, and undocumented topics."""
    guides = _group_guides(chunks)
    claim_map: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for g in guides:
        doc_id, title, body = str(g["doc_id"]), str(g["title"]), str(g["body"])
        for key, val, excerpt in _extract_claims(body):
            claim_map[key].setdefault(doc_id, {"doc_id": doc_id, "title": title, "value": val, "excerpt": excerpt})
    conflicts: list[dict[str, object]] = []
    for key, docs in sorted(claim_map.items()):
        values = {entry["value"] for entry in docs.values()}
        if len(docs) >= 2 and len(values) >= 2:
            conflicts.append({"field": key.title(), "entries": list(docs.values())[:6]})

    duplicates: list[dict[str, object]] = []
    for i in range(len(guides)):
        w1 = guides[i]["words"]
        if not isinstance(w1, set) or len(w1) < 12:
            continue
        for j in range(i + 1, len(guides)):
            w2 = guides[j]["words"]
            if not isinstance(w2, set) or len(w2) < 12:
                continue
            union = len(w1 | w2)
            sim = len(w1 & w2) / union if union else 0.0
            if sim >= 0.65:
                duplicates.append({
                    "similarity": round(sim * 100),
                    "first": {"doc_id": guides[i]["doc_id"], "title": guides[i]["title"]},
                    "second": {"doc_id": guides[j]["doc_id"], "title": guides[j]["title"]},
                })
    duplicates.sort(key=lambda item: int(str(item["similarity"])), reverse=True)

    title_texts = [str(g["title"]).casefold() for g in guides]
    topic_docs: dict[str, list[dict[str, str]]] = defaultdict(list)
    min_mentions = 3 if len(guides) >= 5 else 2
    for g in guides:
        seen: set[str] = set()
        raw_tags = g["tags"] if isinstance(g["tags"], list) else []
        raw_heads = g["headings"] if isinstance(g["headings"], list) else []
        for cand in [*raw_tags, *raw_heads]:
            clean = re.sub(r"\s+", " ", str(cand).strip())
            norm = clean.casefold()
            if len(norm) < 3 or norm in _STOPWORDS or norm in seen:
                continue
            seen.add(norm)
            topic_docs[norm].append({"doc_id": str(g["doc_id"]), "title": str(g["title"]), "label": clean})

    orphan_topics: list[dict[str, object]] = []
    for norm, refs in sorted(topic_docs.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        if len(refs) < min_mentions or any(norm in t for t in title_texts):
            continue
        orphan_topics.append({"topic": refs[0]["label"], "count": len(refs), "guides": [{"doc_id": r["doc_id"], "title": r["title"]} for r in refs[:6]]})

    return {"total_guides": len(guides), "conflicts": conflicts[:20], "duplicates": duplicates[:20], "orphan_topics": orphan_topics[:20]}
