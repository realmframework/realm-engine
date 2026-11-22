"""Executive Impact & ROI Report renderer (.pdf via fpdf2 and widescreen .pptx via python-pptx)."""

import io
from typing import cast

from fpdf import FPDF
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from core.impact_contracts import ImpactLedgerState
from features.impact_ledger.store import compute_roi_summary


def _latin(text: str) -> str:
    return text.replace("—", "-").replace("–", "-").replace("•", "-").replace("€", "EUR ").encode("latin-1", "replace").decode("latin-1")


def _hex_rgb(hex_str: str) -> RGBColor:
    clean = hex_str.lstrip("#")
    return RGBColor(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def render_impact_pdf(state: ImpactLedgerState, title: str, project_names: dict[str, str] | None = None) -> bytes:
    """Render an executive Impact, Time & ROI PDF report."""
    summary = compute_roi_summary(state)
    cur, pmap = str(summary["currency"]), project_names or {}
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(11, 16, 32)
    pdf.cell(0, 10, _latin(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(90, 105, 130)
    roi_str = f"{summary['roi_pct']}%" if summary["roi_pct"] is not None else "N/A"
    kpi_line = f"Hours: {summary['total_hours']}h  |  Cost: {cur} {summary['total_cost']}  |  Value: {cur} {summary['total_value']}  |  Net: {cur} {summary['net_impact']}  |  ROI: {roi_str}"
    pdf.cell(0, 7, _latin(kpi_line), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    by_proj = cast(list[dict[str, object]], summary["by_project"])
    if by_proj:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(11, 16, 32)
        pdf.cell(0, 8, "ROI by Project", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for row in by_proj[:20]:
            pid = str(row["project_id"])
            pname = pmap.get(pid, pid or "General")
            proi = f"{row['roi_pct']}%" if row["roi_pct"] is not None else "N/A"
            pdf.multi_cell(pdf.epw, 6, _latin(f"- {pname}: {row['hours']}h | Cost {cur} {row['cost']} | Value {cur} {row['value']} | ROI {proi}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    if state.impact_entries:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(11, 16, 32)
        pdf.cell(0, 8, "Impact Documentation (Wirksamkeitsdokumentation)", new_x="LMARGIN", new_y="NEXT")
        for imp in state.impact_entries[:30]:
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(15, 23, 42)
            pdf.multi_cell(pdf.epw, 6, _latin(f"[{imp.date}] {imp.what_done}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(55, 65, 81)
            pdf.multi_cell(pdf.epw, 5.5, _latin(f"Effect: {imp.effect}"), new_x="LMARGIN", new_y="NEXT")
            if imp.evidence_notes:
                pdf.multi_cell(pdf.epw, 5, _latin(f"Notes: {imp.evidence_notes[:300]}"), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)

    if state.time_entries:
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(11, 16, 32)
        pdf.cell(0, 8, "Recent Time Entries", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(55, 65, 81)
        for te in state.time_entries[:40]:
            pdf.multi_cell(pdf.epw, 5.5, _latin(f"{te.date}  |  {te.duration_minutes:.0f} min  |  {te.label} ({te.source})"), new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


def render_impact_pptx(state: ImpactLedgerState, title: str, accent_hex: str = "#4BB8E8", project_names: dict[str, str] | None = None) -> bytes:
    """Render a 16:9 widescreen PowerPoint (.pptx) Impact & ROI executive deck."""
    summary = compute_roi_summary(state)
    cur, pmap = str(summary["currency"]), project_names or {}
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]
    accent = _hex_rgb(accent_hex if len(accent_hex) == 7 else "#4BB8E8")
    navy, white, slate = RGBColor(11, 16, 32), RGBColor(238, 242, 248), RGBColor(30, 41, 59)

    s0 = prs.slides.add_slide(blank)
    s0.background.fill.solid()
    s0.background.fill.fore_color.rgb = navy
    tb = s0.shapes.add_textbox(Inches(0.9), Inches(2.2), Inches(11.5), Inches(2.2))
    tf = tb.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    p0.text = title
    p0.font.size, p0.font.bold, p0.font.color.rgb = Pt(40), True, white
    p1 = tf.add_paragraph()
    roi_str = f"{summary['roi_pct']}%" if summary["roi_pct"] is not None else "N/A"
    p1.text = f"Hours: {summary['total_hours']}h  ·  Value: {cur} {summary['total_value']}  ·  Net: {cur} {summary['net_impact']}  ·  ROI: {roi_str}"
    p1.font.size, p1.font.color.rgb = Pt(18), accent

    s1 = prs.slides.add_slide(blank)
    h1 = s1.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.8)).text_frame.paragraphs[0]
    h1.text = "Executive ROI Summary"
    h1.font.size, h1.font.bold, h1.font.color.rgb = Pt(28), True, navy
    b1 = s1.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.2)).text_frame
    b1.word_wrap = True
    by_proj = cast(list[dict[str, object]], summary["by_project"])
    rows = by_proj[:8] or [{"project_id": "", "hours": summary["total_hours"], "cost": summary["total_cost"], "value": summary["total_value"], "roi_pct": summary["roi_pct"]}]
    for idx, row in enumerate(rows):
        p = b1.paragraphs[0] if idx == 0 else b1.add_paragraph()
        pid = str(row["project_id"])
        pname = pmap.get(pid, pid or "General")
        proi = f"{row['roi_pct']}%" if row["roi_pct"] is not None else "N/A"
        p.text = f"• {pname}: {row['hours']}h logged | Cost {cur} {row['cost']} | Value {cur} {row['value']} | ROI {proi}"
        p.font.size, p.font.color.rgb = Pt(17), slate

    if state.impact_entries:
        s2 = prs.slides.add_slide(blank)
        h2 = s2.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.8)).text_frame.paragraphs[0]
        h2.text = "Documented Effects & Outcomes"
        h2.font.size, h2.font.bold, h2.font.color.rgb = Pt(28), True, navy
        b2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.4)).text_frame
        b2.word_wrap = True
        for idx, imp in enumerate(state.impact_entries[:6]):
            p = b2.paragraphs[0] if idx == 0 else b2.add_paragraph()
            p.text = f"• [{imp.date}] {imp.what_done} -> {imp.effect}"
            p.font.size, p.font.color.rgb = Pt(15), slate

    out = io.BytesIO()
    prs.save(out)
    return out.getvalue()
