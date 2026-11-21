"""Local-first active-recall flashcard generator and spaced-repetition progress store."""

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from core.contracts import KnowledgeChunk
from core.db import atomic_write_text, backup_corrupt_file
from core.scope import matches_scope

StudyRating = Literal["hard", "good", "easy"]
PROGRESS_FILENAME = "study_progress.json"
_DEF_RE = re.compile(r"^\s*(?:[-*]\s*)?\*\*([^*\n]{3,80})\*\*\s*[:—-]\s*(.{12,320})$")
_QA_RE = re.compile(r"(?i)^\s*(?:Q|Question)\s*:\s*(.{6,180})$")


def _card_id(doc_id: str, front: str) -> str:
    return hashlib.sha1(f"{doc_id}::{front.strip().lower()}".encode(), usedforsecurity=False).hexdigest()[:12]


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value)) if value is not None else default
    except (ValueError, TypeError):
        return default


def _resolve_store(area_or_file: Path) -> Path:
    return area_or_file if area_or_file.suffix == ".json" else area_or_file / PROGRESS_FILENAME


def _clean_excerpt(text: str, limit: int = 420) -> str:
    plain = re.sub(r"\n{3,}", "\n\n", text.strip())
    return plain if len(plain) <= limit else plain[:limit].rstrip() + "…"


def extract_study_cards(
    chunks: list[KnowledgeChunk],
    doc_id: str | None = None,
    subfolder: str | None = None,
    limit: int = 24,
) -> list[dict[str, object]]:
    """Build deterministic active-recall flashcards from Markdown chunks."""
    cards: list[dict[str, object]] = []
    seen_ids: set[str] = set()
    for chunk in chunks:
        if not matches_scope(chunk, doc_id, subfolder):
            continue
        doc_title, _, sec_title = chunk.title.partition(" — ")
        doc_title, sec_title = doc_title.strip() or chunk.doc_id or "Guide", sec_title.strip()
        lines = [ln.strip() for ln in chunk.content.splitlines() if ln.strip()]

        for line in lines:
            if m := _DEF_RE.match(line):
                front, back = f"What is {m.group(1).strip().rstrip(':')}?", m.group(2).strip()
                cid = _card_id(chunk.doc_id or doc_title, front)
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    cards.append({"id": cid, "front": front, "back": back, "doc_id": chunk.doc_id, "source": doc_title, "tags": list(chunk.tags[:3])})

        for idx, line in enumerate(lines[:-1]):
            if (qm := _QA_RE.match(line)) and lines[idx + 1] and not _QA_RE.match(lines[idx + 1]):
                front = qm.group(1).strip()
                back = re.sub(r"(?i)^(?:A|Answer)\s*:\s*", "", lines[idx + 1]).strip()
                cid = _card_id(chunk.doc_id or doc_title, front)
                if back and cid not in seen_ids:
                    seen_ids.add(cid)
                    cards.append({"id": cid, "front": front, "back": back, "doc_id": chunk.doc_id, "source": doc_title, "tags": list(chunk.tags[:3])})

        if len(chunk.content.strip()) >= 35:
            front = f"{doc_title}: Explain “{sec_title}”" if sec_title and sec_title.lower() != doc_title.lower() else f"Summarize the key points of “{doc_title}”"
            cid = _card_id(chunk.doc_id or doc_title, front)
            if cid not in seen_ids:
                seen_ids.add(cid)
                cards.append({"id": cid, "front": front, "back": _clean_excerpt(chunk.content), "doc_id": chunk.doc_id, "source": doc_title, "tags": list(chunk.tags[:3])})
        if len(cards) >= limit:
            break
    return cards[:limit]


def _read_progress(path: Path, *, strict_io: bool) -> dict[str, dict[str, object]]:
    if path.is_symlink():
        raise ValueError("Study progress file cannot be a symbolic link")
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        if strict_io:
            raise
        return {}
    try:
        raw = json.loads(text)
    except ValueError:
        if strict_io:
            backup_corrupt_file(path)
        return {}
    if not isinstance(raw, dict):
        if strict_io:
            backup_corrupt_file(path)
        return {}
    return {str(k): v for k, v in raw.items() if isinstance(v, dict)}


def load_study_progress(area_dir: Path) -> dict[str, dict[str, object]]:
    try:
        return _read_progress(_resolve_store(area_dir), strict_io=False)
    except ValueError:
        return {}


def record_card_review(area_dir: Path, card_id: str, rating: StudyRating) -> dict[str, object]:
    """Update spaced-repetition schedule for ``card_id`` using 3-tier recall intervals."""
    path = _resolve_store(area_dir)
    progress = _read_progress(path, strict_io=True)
    prev = progress.get(card_id, {})
    prev_box, prev_reviews = _safe_int(prev.get("box"), 0), _safe_int(prev.get("reviews"), 0)
    if rating == "hard":
        box, days = 1, 0
    elif rating == "good":
        box = min(5, max(1, prev_box + 1))
        days = (1, 3, 7, 14, 30)[box - 1]
    else:
        box = min(5, max(2, prev_box + 2))
        days = (3, 7, 14, 30, 60)[box - 1]
    now = datetime.now(UTC)
    entry: dict[str, object] = {
        "card_id": card_id, "box": box, "reviews": prev_reviews + 1, "last_rating": rating,
        "interval_days": days, "due_at": (now + timedelta(days=days)).isoformat(), "updated_at": now.isoformat(),
    }
    progress[card_id] = entry
    atomic_write_text(path, json.dumps(progress, indent=2))
    return entry


def enrich_deck_with_progress(cards: list[dict[str, object]], progress: dict[str, dict[str, object]]) -> dict[str, object]:
    now_iso, enriched, due_count, mastered_count = datetime.now(UTC).isoformat(), [], 0, 0
    for card in cards:
        st = progress.get(str(card["id"]))
        due_at = str(st.get("due_at") or "") if st else ""
        box = _safe_int(st.get("box"), 0) if st else 0
        is_due = not st or due_at <= now_iso
        due_count += int(is_due)
        mastered_count += int(box >= 3)
        enriched.append({**card, "box": box, "due": is_due, "last_rating": str(st.get("last_rating") or "") if st else ""})
    enriched.sort(key=lambda c: (not bool(c["due"]), _safe_int(c.get("box"), 0)))
    return {"cards": enriched, "total_count": len(enriched), "due_count": due_count, "mastered_count": mastered_count}
