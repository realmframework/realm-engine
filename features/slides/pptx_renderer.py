"""Render a DeckSpec into an editable 16:9 widescreen PowerPoint (.pptx) presentation."""

from io import BytesIO
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

from core.work_contracts import DeckSpec, SlideItem

_DARK_BG = RGBColor(11, 16, 32)
_LIGHT_BG = RGBColor(248, 250, 252)
_CARD_BG = RGBColor(255, 255, 255)
_TEXT_DARK = RGBColor(15, 23, 42)
_TEXT_MUTED = RGBColor(100, 116, 139)
_TEXT_LIGHT = RGBColor(238, 242, 248)
_TEXT_SUB_LIGHT = RGBColor(160, 176, 200)
_BORDER_ROW = RGBColor(238, 243, 250)


def _rgb(hex_color: str) -> RGBColor:
    clean = hex_color.lstrip("#")
    return RGBColor(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def _set_slide_bg(slide: object, color: RGBColor) -> None:
    fill = slide.background.fill  # type: ignore[attr-defined]
    fill.solid()
    fill.fore_color.rgb = color


def _add_bar(slide: object, left: float, top: float, width: float, height: float, color: RGBColor) -> None:
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))  # type: ignore[attr-defined]
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _safe_logo(slide: object, logo_path: Path | None, left: float, top: float, height: float) -> None:
    if not logo_path or not logo_path.is_file() or logo_path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        return
    try:
        slide.shapes.add_picture(str(logo_path), Inches(left), Inches(top), height=Inches(height))  # type: ignore[attr-defined]
    except (OSError, ValueError):
        return


def _build_title_slide(prs: object, deck: DeckSpec, accent: RGBColor, glow: RGBColor, logo_path: Path | None) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # type: ignore[attr-defined]
    _set_slide_bg(slide, _DARK_BG)
    _add_bar(slide, 0, 0, 13.333, 0.18, accent)
    _add_bar(slide, 0, 7.36, 13.333, 0.14, glow)
    _safe_logo(slide, logo_path, 0.85, 0.7, 0.72)

    title_box = slide.shapes.add_textbox(Inches(0.85), Inches(2.2), Inches(11.6), Inches(2.2))
    tf = title_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = deck.title
    p.font.name, p.font.size, p.font.bold, p.font.color.rgb = "Calibri", Pt(40), True, _TEXT_LIGHT

    if deck.subtitle:
        sub_box = slide.shapes.add_textbox(Inches(0.85), Inches(4.55), Inches(11.4), Inches(1.0))
        stf = sub_box.text_frame
        stf.word_wrap = True
        sp = stf.paragraphs[0]
        sp.text = deck.subtitle
        sp.font.name, sp.font.size, sp.font.color.rgb = "Calibri", Pt(18), _TEXT_SUB_LIGHT

    foot = slide.shapes.add_textbox(Inches(0.85), Inches(6.65), Inches(6.0), Inches(0.4))
    fp = foot.text_frame.paragraphs[0]
    fp.text = "REALM Engine"
    fp.font.name, fp.font.size, fp.font.color.rgb = "Calibri", Pt(11), accent


def _add_table(slide: object, rows: list[list[str]], top: float, accent: RGBColor) -> None:
    cols = max(1, max(len(r) for r in rows))
    n_rows = min(len(rows), 10)
    row_h = min(0.55, 4.4 / max(1, n_rows))
    tbl_shape = slide.shapes.add_table(n_rows, cols, Inches(0.85), Inches(top), Inches(11.63), Inches(row_h * n_rows))  # type: ignore[attr-defined]
    table = tbl_shape.table
    for r_idx, row in enumerate(rows[:n_rows]):
        is_head = r_idx == 0
        for c_idx in range(cols):
            cell = table.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = accent if is_head else (_CARD_BG if r_idx % 2 == 1 else _BORDER_ROW)
            p = cell.text_frame.paragraphs[0]
            p.text = row[c_idx] if c_idx < len(row) else ""
            p.font.name, p.font.size, p.font.bold = "Calibri", Pt(12 if is_head else 11.5), is_head
            p.font.color.rgb = _DARK_BG if is_head else _TEXT_DARK


def _build_content_slide(prs: object, item: SlideItem, idx: int, total: int, accent: RGBColor, logo_path: Path | None) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # type: ignore[attr-defined]
    _set_slide_bg(slide, _LIGHT_BG)
    _add_bar(slide, 0, 0, 13.333, 0.12, accent)
    _safe_logo(slide, logo_path, 12.15, 0.32, 0.42)

    head = slide.shapes.add_textbox(Inches(0.85), Inches(0.45), Inches(10.9), Inches(0.85))
    htf = head.text_frame
    htf.word_wrap = True
    hp = htf.paragraphs[0]
    hp.text = item.title
    hp.font.name, hp.font.size, hp.font.bold, hp.font.color.rgb = "Calibri", Pt(26), True, _TEXT_DARK
    _add_bar(slide, 0.85, 1.32, 1.4, 0.05, accent)

    body_top = 1.62
    if item.bullets:
        b_height = 1.6 if item.table_rows else 5.0
        box = slide.shapes.add_textbox(Inches(0.85), Inches(body_top), Inches(11.63), Inches(b_height))
        btf = box.text_frame
        btf.word_wrap = True
        font_pt = 16 if len(item.bullets) >= 5 else 18
        for b_idx, bullet in enumerate(item.bullets):
            bp = btf.paragraphs[0] if b_idx == 0 else btf.add_paragraph()
            bp.text = f"•  {bullet}"
            bp.space_after = Pt(10 if font_pt == 16 else 14)
            bp.font.name, bp.font.size, bp.font.color.rgb = "Calibri", Pt(font_pt), _TEXT_DARK
        body_top += 1.75
    if item.table_rows:
        _add_table(slide, item.table_rows, body_top, accent)

    num = slide.shapes.add_textbox(Inches(10.8), Inches(6.92), Inches(1.7), Inches(0.35))
    np = num.text_frame.paragraphs[0]
    np.text = f"{idx} / {total}"
    np.alignment = PP_ALIGN.RIGHT
    np.font.name, np.font.size, np.font.color.rgb = "Calibri", Pt(10.5), _TEXT_MUTED

    if item.speaker_notes:
        slide.notes_slide.notes_text_frame.text = item.speaker_notes


def render_pptx(deck: DeckSpec, logo_path: Path | None = None) -> bytes:
    """Build a complete 16:9 .pptx file in memory and return its bytes."""
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    accent, glow = _rgb(deck.accent_hex), _rgb(deck.glow_hex)
    total = len(deck.slides)
    for idx, item in enumerate(deck.slides, 1):
        if item.is_title_slide:
            _build_title_slide(prs, deck, accent, glow, logo_path)
        else:
            _build_content_slide(prs, item, idx, total, accent, logo_path)
    buf = BytesIO()
    prs.save(buf)
    return buf.getvalue()
