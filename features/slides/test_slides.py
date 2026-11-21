"""Unit and route tests for native 16:9 PowerPoint (.pptx) and PDF slide deck generation."""

from io import BytesIO
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pptx import Presentation

from features.slides.router import build_router
from features.slides.service import (
    PDF_MIME,
    PPTX_MIME,
    export_deck_bytes,
    markdown_to_deck,
)

SAMPLE_REPORT = """# Quarterly Strategy Report

## Executive Summary
- Revenue efficiency rose 18% after process simplification.
- Customer onboarding time dropped from 14 days to 5 days.
Speaker Notes: Emphasize the onboarding speed win during Q&A.

---

## Comparison Matrix
| Initiative | Effort | Measured Effect |
| --- | --- | --- |
| Automation | 12h | -4h/week saved |
| Templates | 6h | +30% faster drafts |

## Deep Dive Items
- Point one with detail
- Point two with detail
- Point three with detail
- Point four with detail
- Point five with detail
- Point six with detail
- Point seven overflows cleanly to a continuation slide
"""


def test_markdown_to_deck_splits_overflow_extracts_tables_and_notes() -> None:
    deck = markdown_to_deck(
        "Quarterly Strategy Report",
        SAMPLE_REPORT,
        subtitle="Q4 Review",
        citations=["Internal Memo A", "Client Feedback B", "Internal Memo A"],
        accent_hex="#10B981",
        glow_hex="#06B6D4",
    )
    assert deck.slides[0].is_title_slide is True and deck.slides[0].title == "Quarterly Strategy Report"
    titles = [s.title for s in deck.slides]
    assert "Executive Summary" in titles
    assert "Comparison Matrix" in titles
    assert "Deep Dive Items" in titles and "Deep Dive Items (cont.)" in titles
    assert titles[-1] == "Sources & References"
    summary_slide = next(s for s in deck.slides if s.title == "Executive Summary")
    assert "onboarding speed win" in summary_slide.speaker_notes
    matrix_slide = next(s for s in deck.slides if s.title == "Comparison Matrix")
    assert len(matrix_slide.table_rows) == 3 and matrix_slide.table_rows[0] == ["Initiative", "Effort", "Measured Effect"]
    assert len(deck.slides[-1].bullets) == 2


def test_render_pptx_and_pdf_are_valid_widescreen_binaries(tmp_path: Path) -> None:
    pptx_bytes, mime, ext, deck = export_deck_bytes(
        "Quarterly Strategy Report",
        SAMPLE_REPORT,
        subtitle="Q4 Review",
        citations=["Source One"],
        accent_hex="#A855F7",
        fmt="pptx",
    )
    assert mime == PPTX_MIME and ext == ".pptx" and pptx_bytes[:2] == b"PK"
    prs = Presentation(BytesIO(pptx_bytes))
    assert len(prs.slides) == len(deck.slides)
    assert prs.slide_width is not None and prs.slide_height is not None and prs.slide_width > prs.slide_height
    summary_prs_slide = prs.slides[1]
    notes_tf = summary_prs_slide.notes_slide.notes_text_frame
    assert notes_tf is not None and "onboarding speed win" in notes_tf.text
    table_slide = prs.slides[2]
    assert any(getattr(shape, "has_table", False) for shape in table_slide.shapes)

    pdf_bytes, pdf_mime, pdf_ext, _ = export_deck_bytes(
        "Quarterly Strategy Report",
        SAMPLE_REPORT,
        subtitle="Q4 Review",
        citations=["Source One"],
        fmt="pdf",
    )
    assert pdf_mime == PDF_MIME and pdf_ext == ".pdf" and pdf_bytes.startswith(b"%PDF-")


def test_slides_router_serves_pptx_pdf_and_rejects_empty() -> None:
    app = FastAPI()

    def _resolve(_req: object, body: dict[str, object]) -> tuple[str, str, str, list[str], Path | None, str, str]:
        return str(body.get("title") or "Deck"), str(body.get("markdown") or ""), "Sub", ["Ref 1"], None, "#4BB8E8", "#6366F1"

    app.include_router(build_router(_resolve))
    client = TestClient(app)

    assert client.post("/api/export/slides", json={"title": "Empty", "markdown": "   "}).status_code == 400
    r_pptx = client.post("/api/export/slides", json={"title": "My Report", "markdown": "## Slide 1\n- Hello", "format": "pptx"})
    assert r_pptx.status_code == 200 and r_pptx.headers["content-type"] == PPTX_MIME
    assert "my-report-slides.pptx" in r_pptx.headers["content-disposition"] and r_pptx.content[:2] == b"PK"

    r_pdf = client.post("/api/export/slides", json={"title": "My Report", "markdown": "## Slide 1\n- Hello", "format": "pdf"})
    assert r_pdf.status_code == 200 and r_pdf.headers["content-type"] == PDF_MIME
    assert r_pdf.content.startswith(b"%PDF-")
