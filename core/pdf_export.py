"""Cross-platform vector PDF export for individual AI outputs, blueprints, and full chats."""

import re
from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF

from core.contracts import ChatSession

_FONT_CANDIDATES = ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/Library/Fonts/Arial Unicode.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "C:/Windows/Fonts/arial.ttf")
_BOLD_CANDIDATES = ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf")


def _find_font(paths: tuple[str, ...]) -> Path | None:
    return next((Path(p) for p in paths if Path(p).is_file()), None)


def _clean(text: str, uni: bool) -> str:
    cleaned = re.sub(r"[*_`]+", "", re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text))
    return cleaned if uni else cleaned.encode("latin-1", errors="replace").decode("latin-1")


def _new_pdf(title: str, subtitle: str, logo_path: Path | None) -> tuple[FPDF, str, bool]:
    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(16, 16, 16)
    regular, bold = _find_font(_FONT_CANDIDATES), _find_font(_BOLD_CANDIDATES)
    family, uni = "Helvetica", False
    if regular is not None:
        pdf.add_font("RealmSans", "", str(regular))
        pdf.add_font("RealmSans", "B", str(bold or regular))
        family, uni = "RealmSans", True
    pdf.add_page()
    pdf.set_fill_color(11, 16, 32)
    pdf.rect(0, 0, 210, 26, style="F")
    x_text = 16
    if logo_path and logo_path.is_file() and logo_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        try:
            pdf.image(str(logo_path), x=16, y=6, h=14)
            x_text = 34
        except RuntimeError:
            x_text = 16
    pdf.set_xy(x_text, 6.5)
    pdf.set_text_color(238, 242, 248)
    pdf.set_font(family, "B", 14)
    pdf.cell(0, 7, _clean(title[:90], uni), new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(x_text)
    pdf.set_text_color(160, 176, 200)
    pdf.set_font(family, "", 8.5)
    meta = subtitle or f"REALM Engine · Exported {datetime.now(UTC):%Y-%m-%d %H:%M UTC}"
    pdf.cell(0, 5, _clean(meta, uni), new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(32)
    pdf.set_text_color(22, 30, 46)
    return pdf, family, uni


def _write_table(pdf: FPDF, rows: list[list[str]], family: str, uni: bool) -> None:
    if not rows:
        return
    cols = max(len(r) for r in rows)
    col_w = 178.0 / max(1, cols)
    for r_idx, row in enumerate(rows):
        is_head = r_idx == 0
        pdf.set_fill_color(*(238, 243, 250) if is_head else (255, 255, 255))
        pdf.set_font(family, "B" if is_head else "", 8.5)
        if pdf.get_y() > 265:
            pdf.add_page()
        for cell in row + [""] * (cols - len(row)):
            pdf.cell(col_w, 6.5, _clean(cell[:48], uni), border=1, fill=is_head)
        pdf.ln(6.5)
    pdf.ln(2)


def _mc(pdf: FPDF, h: float, text: str, fill: bool = False) -> None:
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(pdf.epw, h, text, fill=fill, new_x="LMARGIN", new_y="NEXT")


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
            _mc(pdf, 4.8, _clean(raw or " ", uni), fill=True)
        elif not stripped:
            pdf.ln(2.2)
        elif stripped.startswith("|") and "|" in stripped[1:]:
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
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
        pdf.set_x(pdf.l_margin)
        pdf.cell(0, 6, "Sources & Citations", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(family, "", 9)
        pdf.set_text_color(71, 85, 105)
        for idx, cite in enumerate(dict.fromkeys(citations), 1):
            _mc(pdf, 4.8, _clean(f"[{idx}] {cite}", uni))
    return bytes(pdf.output())


def render_chat_pdf(session: ChatSession, logo_path: Path | None = None) -> bytes:
    sections, all_citations = [], []
    for idx, turn in enumerate(session.turns, 1):
        head = f"## Turn {idx}: {turn.format_name or 'Conversation'}"
        answer = turn.tutor.answer if turn.tutor else "Search results only."
        sections.append(f"{head}\n\n**Question:** {turn.query}\n\n{answer}")
        if turn.tutor:
            all_citations.extend(turn.tutor.cited_titles)
    subtitle = f"REALM Engine · {len(session.turns)} turns · Updated {session.updated_at[:16].replace('T', ' ')}"
    return render_markdown_pdf(session.title or "Conversation", "\n\n".join(sections), subtitle=subtitle, citations=all_citations, logo_path=logo_path)
