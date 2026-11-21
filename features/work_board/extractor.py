"""Extract actionable Kanban tasks from chat turns, Library guides, or raw notes."""

import json
import re
from collections.abc import AsyncIterator, Callable

from core.contracts import TutorConfig
from core.work_contracts import PriorityLevel

StreamMessagesFn = Callable[..., AsyncIterator[dict[str, object]]]
_DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_BULLET_RE = re.compile(r"^\s*(?:[-*•]\s*(?:\[\s*\]\s*)?|\d+[.)]\s+)(.+)$")
_PREFIX_RE = re.compile(r"^\s*(?:todo|action|task|next step|aufgabe|to-do|tarea)\s*[:\-]\s*(.+)$", re.IGNORECASE)
_URGENT_RE = re.compile(r"\b(urgent|asap|critical|dringend|sofort|urgente)\b", re.IGNORECASE)
_HIGH_RE = re.compile(r"\b(high|important|priority|wichtig|priorität|importante)\b", re.IGNORECASE)
_LOW_RE = re.compile(r"\b(low|later|optional|später|baja)\b", re.IGNORECASE)


def _clean_title(raw: str) -> str:
    cleaned = re.sub(r"[*_`]+", "", raw).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:180]


def _infer_priority(text: str) -> PriorityLevel:
    if _URGENT_RE.search(text):
        return "urgent"
    if _HIGH_RE.search(text):
        return "high"
    if _LOW_RE.search(text):
        return "low"
    return "medium"


def extract_tasks_deterministic(text: str, max_items: int = 12) -> list[dict[str, str]]:
    """Parse checklist items, action prefixes, and numbered/bulleted steps cleanly offline."""
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or re.match(r"^[-*]\s*\[[xX]\]", line):
            continue
        match = _PREFIX_RE.match(line) or _BULLET_RE.match(line)
        if not match:
            continue
        body = _clean_title(match.group(1))
        if len(body) < 4 or body.lower() in seen:
            continue
        seen.add(body.lower())
        date_hit = _DATE_RE.search(body)
        candidates.append({"title": body, "description": "", "priority": _infer_priority(body), "due_date": date_hit.group(1) if date_hit else ""})
        if len(candidates) >= max_items:
            break
    if not candidates and text.strip():
        first_sentence = _clean_title(re.split(r"[.!?\n]", text.strip())[0])
        if len(first_sentence) >= 4:
            candidates.append({"title": first_sentence, "description": text.strip()[:400], "priority": "medium", "due_date": ""})
    return candidates


def _parse_llm_tasks(raw_text: str, max_items: int = 12) -> list[dict[str, str]]:
    block = re.search(r"<tasks_json>\s*(\[.*?\])\s*</tasks_json>", raw_text, re.DOTALL)
    json_str = block.group(1) if block else (raw_text[raw_text.find("[") : raw_text.rfind("]") + 1] if "[" in raw_text and "]" in raw_text else "")
    if not json_str:
        return []
    try:
        parsed = json.loads(json_str)
    except ValueError:
        return []
    if not isinstance(parsed, list):
        return []
    out: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        title = _clean_title(str(item.get("title") or ""))
        if len(title) < 3:
            continue
        prio_raw = str(item.get("priority") or "medium").lower().strip()
        prio = prio_raw if prio_raw in {"low", "medium", "high", "urgent"} else "medium"
        due = str(item.get("due_date") or "").strip()
        if due and not _DATE_RE.fullmatch(due):
            due = ""
        out.append({"title": title, "description": str(item.get("description") or "").strip()[:400], "priority": prio, "due_date": due})
        if len(out) >= max_items:
            break
    return out


async def extract_tasks_with_ai(
    text: str,
    stream_messages: StreamMessagesFn | None,
    tutor_config: TutorConfig | None,
    *,
    language: str = "en",
    max_items: int = 12,
) -> tuple[list[dict[str, str]], str]:
    """Extract structured tasks via LLM when available, falling back to deterministic parser."""
    trimmed = text.strip()[:6000]
    if not trimmed:
        return [], "deterministic"
    if stream_messages is None or tutor_config is None:
        return extract_tasks_deterministic(trimmed, max_items=max_items), "deterministic"
    lang_hint = {"de": "German", "es": "Spanish"}.get(language, "the same language as the input")
    system = (
        f"Extract concrete, actionable tasks from the text in {lang_hint}. "
        "Reply ONLY with a JSON array wrapped in <tasks_json>...</tasks_json>. "
        'Each item: {"title": string, "description": string, "priority": "low"|"medium"|"high"|"urgent", "due_date": "YYYY-MM-DD" or ""}. '
        f"Return at most {max_items} high-signal tasks."
    )
    buf: list[str] = []
    try:
        async for ev in stream_messages([{"role": "system", "content": system}, {"role": "user", "content": trimmed}], tutor_config):
            if ev.get("event") == "token":
                buf.append(str(ev.get("text") or ""))
    except Exception:
        return extract_tasks_deterministic(trimmed, max_items=max_items), "deterministic"
    parsed = _parse_llm_tasks("".join(buf), max_items=max_items)
    if parsed:
        return parsed, "ai"
    return extract_tasks_deterministic(trimmed, max_items=max_items), "deterministic"
