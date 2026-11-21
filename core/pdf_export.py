"""Cross-platform vector PDF export for individual AI outputs, blueprints, and full chats."""

import os
import re
from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF

from core.contracts import ChatSession

_WIN_FONTS = Path(os.environ.get("WINDIR") or os.environ.get("SYSTEMROOT") or "C:/Windows") / "Fonts"
_FONT_CANDIDATES = ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", str(_WIN_FONTS / "arial.ttf"))
_BOLD_CANDIDATES = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", str(_WIN_FONTS / "arialbd.ttf"))
_TABLE_SPLIT_RE = re.compile(r"(?<!\\)\|")

def _find_font(paths: tuple[str, ...]) -> Path | None:
    return next((Path(p) for p in paths if Path(p).is_file()), None)

def _encode(text: str, uni: bool) -> str:
    return text if uni else text.encode("latin-1", errors="replace").decode("latin-1")

def _clean(text: str, uni: bool, *, raw_code: bool = False) -> str:
    if raw_code:
        return _encode(text, uni)
    c = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    c = re.sub(r"(^|[\s(])_([^_\n]+)_(?=$|[\s.,;:!?)\]])", r"\1\2", re.sub(r"(^|[^*])\*([^*\n]+)\*(?!\*)", r"\1\2", re.sub(r"\*\*([^*]+)\*\*", r"\1", c))).replace("`", "")
    return _encode(c, uni)

def _mc(pdf: FPDF, h: float, text: str, fill: bool = False) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, text, fill=fill, new_x="LMARGIN", new_y="NEXT")


def _new_pdf(title: str, subtitle: str, logo_path: Path | None) -> tuple[FPDF, str, bool]:
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(16, 16, 16)
    regular, bold, family, uni = _find_font(_FONT_CANDIDATES), _find_font(_BOLD_CANDIDATES), "Helvetica", False
    if regular is not None:
        try:
            pdf.add_font("RealmSans", "", str(regular))
            pdf.add_font("RealmSans", "B", str(bold or regular))
            family, uni = "RealmSans", True
        except (RuntimeError, OSError, ValueError):
            family, uni = "Helvetica", False
    pdf.add_page()
    x_text = 16
    if logo_path and logo_path.is_file() and logo_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        try:
            pdf.image(str(logo_path), x=16, y=14, h=11)
            x_text = 31
        except (RuntimeError, OSError, ValueError):
            x_text = 16
    pdf.set_xy(x_text, 14)
    pdf.set_text_color(15, 23, 42)
    pdf.set_font(family, "B", 15.5)
    pdf.cell(0, 7, _clean(re.sub(r"[\r\n]+", " ", title).strip()[:90], uni), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x_text)
    pdf.set_text_color(100, 116, 139)
    pdf.set_font(family, "", 8.5)
    pdf.cell(0, 5, _clean(re.sub(r"[\r\n]+", " ", subtitle or datetime.now(UTC).strftime("%Y-%m-%d")).strip()[:120], uni), new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(203, 213, 225)
    y_rule = max(pdf.get_y() + 2, 28)
    pdf.line(16, y_rule, 194, y_rule)
    pdf.set_y(y_rule + 5)
    pdf.set_text_color(22, 30, 46)
    return pdf, family, uni


def _write_table(pdf: FPDF, rows: list[list[str]], family: str, uni: bool) -> None:
    if not rows:
        return
    cols = max(len(r) for r in rows)
    col_w = 178.0 / max(1, cols)
    max_chars = max(8, int(col_w / 1.9))
    for r_idx, row in enumerate(rows):
        is_head = r_idx == 0
        pdf.set_fill_color(*(238, 243, 250) if is_head else (255, 255, 255))
        pdf.set_font(family, "B" if is_head else "", 8.5)
        if pdf.get_y() > 265:
            pdf.add_page()
        for cell in row + [""] * (cols - len(row)):
            val = _clean(cell, uni)
            pdf.cell(col_w, 6.5, val[: max_chars - 1].rstrip() + "…" if len(val) > max_chars else val, border=1, fill=is_head)
        pdf.ln(6.5)
    pdf.ln(2)


def _write_markdown(pdf: FPDF, markdown: str, family: str, uni: bool) -> None:
    lines, i, in_code = markdown.replace("\r\n", "\n").splitlines(), 0, False
    while i < len(lines):
        raw, stripped = lines[i], lines[i].strip()
        if stripped.startswith("```"):
            in_code, i = not in_code, i + 1
            continue
        if in_code:
            pdf.set_fill_color(242, 245, 250)
            pdf.set_font(family, "", 8.5)
            _mc(pdf, 4.8, _clean(raw or " ", uni, raw_code=True), fill=True)
        elif not stripped:
            pdf.ln(2.2)
        elif stripped.startswith("|") and "|" in stripped[1:]:
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.replace("\\|", "|").strip() for c in _TABLE_SPLIT_RE.split(lines[i].strip().removeprefix("|").removesuffix("|"))]
                if not all(re.fullmatch(r"[:\- ]+", c or "-") for c in cells):
                    rows.append(cells)
                i += 1
            _write_table(pdf, rows, family, uni)
            continue
        elif heading := re.match(r"^(#{1,3})\s+(.*)$", stripped):
            lvl = len(heading.group(1))
            pdf.ln(2.5 if lvl > 1 else 3.5)
            pdf.set_text_color(*(11, 66, 108) if lvl <= 2 else (30, 41, 59))
            pdf.set_font(family, "B", 13 if lvl == 1 else (11.2 if lvl == 2 else 10.2))
            _mc(pdf, 6, _clean(heading.group(2), uni))
            pdf.set_text_color(22, 30, 46)
        elif bullet := re.match(r"^(?:[-*+]|\d+\.)\s+(.*)$", stripped):
            pdf.set_font(family, "", 9.8)
            _mc(pdf, 5.2, _clean(("•  " if uni else "-  ") + bullet.group(1), uni))
        else:
            pdf.set_font(family, "", 9.8)
            _mc(pdf, 5.3, _clean(stripped, uni))
        i += 1


def render_markdown_pdf(title: str, markdown: str, subtitle: str = "", citations: list[str] | None = None, logo_path: Path | None = None) -> bytes:
    pdf, family, uni = _new_pdf(title or "REALM Export", subtitle, logo_path)
    _write_markdown(pdf, markdown, family, uni)
    if citations:
        pdf.ln(4)
        pdf.set_font(family, "B", 10.5)
        pdf.set_text_color(11, 66, 108)
        _mc(pdf, 6, "Sources & Citations")
        pdf.set_font(family, "", 9)
        pdf.set_text_color(71, 85, 105)
        for idx, cite in enumerate(dict.fromkeys(citations), 1):
            _mc(pdf, 4.8, _clean(f"[{idx}] {cite}", uni))
    return bytes(pdf.output())


def render_chat_pdf(session: ChatSession, logo_path: Path | None = None) -> bytes:
    sections = [f"## Turn {i}{f' · {t.agent_name}' if t.agent_name else ''}: {t.format_name or 'Conversation'}\n\n**Question:** {t.query}\n\n{t.tutor.answer if t.tutor else 'Search results only.'}" for i, t in enumerate(session.turns, 1)]
    cites = [c for t in session.turns if t.tutor for c in t.tutor.cited_titles]
    return render_markdown_pdf(session.title or "Conversation", "\n\n".join(sections), subtitle=f"{len(session.turns)} turns · {session.updated_at[:10]}", citations=cites, logo_path=logo_path)
