"""Render a DeckSpec into a 16:9 widescreen PDF presentation via fpdf2."""

from pathlib import Path

from fpdf import FPDF

from core.pdf_fonts import draw_pdf_logo, hex_to_rgb, pdf_encode, setup_pdf_unicode_font
from core.work_contracts import DeckSpec, SlideItem


def _enc(text: str, uni: bool) -> str:
    return pdf_encode(text, uni)


def _init_pdf() -> tuple[FPDF, str, bool]:
    pdf = FPDF(orientation="L", unit="mm", format=(167.0, 297.0))
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(18, 14, 18)
    fam, uni = setup_pdf_unicode_font(pdf, "SlideSans")
    return pdf, fam, uni


def _draw_logo(pdf: FPDF, logo_path: Path | None, x: float, y: float, h: float) -> None:
    draw_pdf_logo(pdf, logo_path, x, y, h)


def _draw_title(pdf: FPDF, deck: DeckSpec, fam: str, uni: bool, acc: tuple[int, int, int], glow: tuple[int, int, int], logo: Path | None) -> None:
    pdf.add_page()
    pdf.set_fill_color(11, 16, 32)
    pdf.rect(0, 0, 297, 167, style="F")
    pdf.set_fill_color(*acc)
    pdf.rect(0, 0, 297, 4, style="F")
    pdf.set_fill_color(*glow)
    pdf.rect(0, 164, 297, 3, style="F")
    _draw_logo(pdf, logo, 18, 16, 15)
    pdf.set_xy(18, 52)
    pdf.set_text_color(238, 242, 248)
    pdf.set_font(fam, "B", 28)
    pdf.multi_cell(260, 13, _enc(deck.title, uni), new_x="LMARGIN", new_y="NEXT")
    if deck.subtitle:
        pdf.set_xy(18, max(pdf.get_y() + 6, 92))
        pdf.set_text_color(160, 176, 200)
        pdf.set_font(fam, "", 13)
        pdf.multi_cell(250, 7, _enc(deck.subtitle, uni), new_x="LMARGIN", new_y="NEXT")
    pdf.set_xy(18, 146)
    pdf.set_text_color(*acc)
    pdf.set_font(fam, "B", 9.5)
    pdf.cell(60, 6, "REALM Engine")


def _draw_table(pdf: FPDF, rows: list[list[str]], fam: str, uni: bool, acc: tuple[int, int, int]) -> None:
    cols = max(1, max(len(r) for r in rows))
    col_w = 261.0 / cols
    max_ch = max(10, int(col_w / 2.2))
    for r_idx, row in enumerate(rows[:9]):
        if pdf.get_y() > 146:
            break
        is_head = r_idx == 0
        pdf.set_fill_color(*(acc if is_head else ((255, 255, 255) if r_idx % 2 == 1 else (238, 243, 250))))
        pdf.set_text_color(15, 23, 42)
        pdf.set_font(fam, "B" if is_head else "", 9.5)
        pdf.set_x(18)
        for c_idx in range(cols):
            val = _enc(row[c_idx] if c_idx < len(row) else "", uni)
            pdf.cell(col_w, 8.0, val[: max_ch - 1].rstrip() + "…" if len(val) > max_ch else val, border=1, fill=True)
        pdf.ln(8.0)


def _draw_content(pdf: FPDF, item: SlideItem, idx: int, total: int, fam: str, uni: bool, acc: tuple[int, int, int], logo: Path | None) -> None:
    pdf.add_page()
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(0, 0, 297, 167, style="F")
    pdf.set_fill_color(*acc)
    pdf.rect(0, 0, 297, 3, style="F")
    _draw_logo(pdf, logo, 268, 8, 9.5)

    pdf.set_xy(18, 11)
    pdf.set_text_color(15, 23, 42)
    pdf.set_font(fam, "B", 19)
    pdf.multi_cell(242, 9, _enc(item.title, uni), new_x="LMARGIN", new_y="NEXT")
    pdf.set_fill_color(*acc)
    pdf.rect(18, max(pdf.get_y() + 1.5, 24), 32, 1.2, style="F")
    pdf.set_y(max(pdf.get_y() + 7, 31))

    if item.bullets:
        pdf.set_text_color(22, 30, 46)
        pdf.set_font(fam, "", 12 if len(item.bullets) >= 5 else 13)
        bullet_prefix = "•  " if uni else "-  "
        for b in item.bullets:
            if pdf.get_y() > 144:
                break
            pdf.set_x(18)
            pdf.multi_cell(261, 7.2, _enc(bullet_prefix + b, uni), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2.2)
    if item.table_rows:
        pdf.ln(2)
        _draw_table(pdf, item.table_rows, fam, uni, acc)

    pdf.set_xy(245, 154)
    pdf.set_text_color(100, 116, 139)
    pdf.set_font(fam, "", 9)
    pdf.cell(34, 6, f"{idx} / {total}", align="R")


def render_slides_pdf(deck: DeckSpec, logo_path: Path | None = None) -> bytes:
    """Render a 16:9 landscape PDF slide deck matching the PowerPoint layout."""
    pdf, fam, uni = _init_pdf()
    acc, glow = hex_to_rgb(deck.accent_hex), hex_to_rgb(deck.glow_hex)
    total = len(deck.slides)
    for idx, item in enumerate(deck.slides, 1):
        if item.is_title_slide:
            _draw_title(pdf, deck, fam, uni, acc, glow, logo_path)
        else:
            _draw_content(pdf, item, idx, total, fam, uni, acc, logo_path)
    return bytes(pdf.output())
