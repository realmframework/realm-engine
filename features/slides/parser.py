"""Convert structured Markdown reports, guides, or chats into clean SlideItem sequences."""

import re

from core.work_contracts import DeckSpec, SlideItem

_TABLE_SPLIT_RE = re.compile(r"(?<!\\)\|")
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_NOTE_RE = re.compile(r"^(?:>\s*)?(?:speaker\s*notes?|presenter\s*notes?|notizen|notas)\s*:\s*(.*)$", re.IGNORECASE)
_MAX_BULLETS_PER_SLIDE = 6


def clean_slide_text(text: str) -> str:
    """Strip Markdown inline formatting into crisp presentation copy."""
    c = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text.strip())
    c = re.sub(r"\*\*([^*]+)\*\*", r"\1", c)
    c = re.sub(r"(^|[^*])\*([^*\n]+)\*(?!\*)", r"\1\2", c)
    c = re.sub(r"(^|[\s(])_([^_\n]+)_(?=$|[\s.,;:!?)\]])", r"\1\2", c)
    return re.sub(r"\s+", " ", c.replace("`", "")).strip()


def _flush_slide(out: list[SlideItem], title: str, bullets: list[str], table_rows: list[list[str]], notes: list[str]) -> None:
    clean_title = clean_slide_text(title)[:140] or "Overview"
    clean_bullets = [clean_slide_text(b)[:220] for b in bullets if clean_slide_text(b)]
    clean_notes = "\n".join(n.strip() for n in notes if n.strip())[:1800]
    if not clean_bullets and not table_rows and not clean_notes:
        return
    if table_rows:
        out.append(SlideItem(title=clean_title, bullets=clean_bullets[:3], table_rows=table_rows[:12], speaker_notes=clean_notes))
        clean_bullets = clean_bullets[3:]
        clean_notes = ""
    if not clean_bullets:
        if clean_notes and not table_rows:
            out.append(SlideItem(title=clean_title, bullets=[clean_notes[:220]], speaker_notes=clean_notes))
        return
    for chunk_idx in range(0, len(clean_bullets), _MAX_BULLETS_PER_SLIDE):
        suffix = "" if chunk_idx == 0 else " (cont.)"
        out.append(
            SlideItem(
                title=(clean_title[:130] + suffix),
                bullets=clean_bullets[chunk_idx : chunk_idx + _MAX_BULLETS_PER_SLIDE],
                speaker_notes=clean_notes if chunk_idx == 0 else "",
            )
        )


def _split_long_paragraph(paragraph: str) -> list[str]:
    clean = clean_slide_text(paragraph)
    if len(clean) <= 180:
        return [clean] if clean else []
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean) if s.strip()]
    grouped: list[str] = []
    for sent in sentences:
        if grouped and len(grouped[-1]) + len(sent) + 1 <= 190:
            grouped[-1] = f"{grouped[-1]} {sent}"
        else:
            grouped.append(sent[:210])
    return grouped[:6]


def markdown_to_deck(
    title: str,
    markdown: str,
    subtitle: str = "",
    citations: list[str] | None = None,
    accent_hex: str = "#4BB8E8",
    glow_hex: str = "#6366F1",
) -> DeckSpec:
    """Parse any Markdown report or chat into a balanced 16:9 DeckSpec."""
    safe_title = clean_slide_text(title)[:140] or "REALM Presentation"
    safe_sub = clean_slide_text(subtitle)[:180]
    accent = accent_hex if _HEX_RE.fullmatch(accent_hex or "") else "#4BB8E8"
    glow = glow_hex if _HEX_RE.fullmatch(glow_hex or "") else "#6366F1"
    slides: list[SlideItem] = [SlideItem(title=safe_title, bullets=[safe_sub] if safe_sub else [], is_title_slide=True)]
    cur_title, bullets, table_rows, notes = "", [], [], []
    lines, i, in_code = markdown.replace("\r\n", "\n").splitlines(), 0, False

    while i < len(lines):
        raw, stripped = lines[i], lines[i].strip()
        if stripped.startswith("```"):
            in_code, i = not in_code, i + 1
            continue
        if in_code:
            if stripped:
                bullets.append(stripped[:160])
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if re.fullmatch(r"[-*_]{3,}", stripped):
            _flush_slide(slides, cur_title or safe_title, bullets, table_rows, notes)
            cur_title, bullets, table_rows, notes, i = "", [], [], [], i + 1
            continue
        if note_m := _NOTE_RE.match(stripped):
            if note_m.group(1).strip():
                notes.append(clean_slide_text(note_m.group(1)))
            i += 1
            continue
        if h_match := re.match(r"^(#{1,3})\s+(.*)$", stripped):
            lvl, h_text = len(h_match.group(1)), clean_slide_text(h_match.group(2))
            if lvl == 1 and not cur_title and not bullets and not table_rows and len(slides) == 1:
                if safe_title == "REALM Presentation":
                    slides[0] = slides[0].model_copy(update={"title": h_text[:140]})
                i += 1
                continue
            _flush_slide(slides, cur_title or safe_title, bullets, table_rows, notes)
            cur_title, bullets, table_rows, notes, i = h_text, [], [], [], i + 1
            continue
        if stripped.startswith("|") and "|" in stripped[1:]:
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [clean_slide_text(c.replace("\\|", "|"))[:70] for c in _TABLE_SPLIT_RE.split(lines[i].strip().removeprefix("|").removesuffix("|"))]
                if cells and not all(re.fullmatch(r"[:\- ]+", c or "-") for c in cells):
                    table_rows.append(cells[:6])
                i += 1
            continue
        if b_match := re.match(r"^(?:[-*+]|\d+\.)\s+(.*)$", stripped):
            bullets.append(b_match.group(1))
        elif stripped.startswith(">"):
            q_text = stripped.lstrip(">").strip()
            if q_text:
                notes.append(clean_slide_text(q_text))
                bullets.append(q_text)
        else:
            bullets.extend(_split_long_paragraph(raw))
        i += 1

    _flush_slide(slides, cur_title or safe_title, bullets, table_rows, notes)
    if len(slides) == 1:
        slides.append(SlideItem(title=safe_title, bullets=[clean_slide_text(markdown)[:220] or "No content available."]))
    unique_cites = [clean_slide_text(c)[:180] for c in dict.fromkeys(citations or []) if clean_slide_text(c)]
    if unique_cites:
        slides.append(SlideItem(title="Sources & References", bullets=[f"[{idx}] {c}" for idx, c in enumerate(unique_cites[:10], 1)]))
    return DeckSpec(title=slides[0].title, subtitle=safe_sub, accent_hex=accent, glow_hex=glow, slides=slides[:60])
