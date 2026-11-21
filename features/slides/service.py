"""Slide deck slice facade combining Markdown parsing with .pptx and 16:9 PDF renderers."""

from pathlib import Path
from typing import Literal

from core.work_contracts import DeckSpec
from features.slides.parser import markdown_to_deck
from features.slides.pdf_renderer import render_slides_pdf
from features.slides.pptx_renderer import render_pptx

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
PDF_MIME = "application/pdf"


def export_deck_bytes(
    title: str,
    markdown: str,
    *,
    subtitle: str = "",
    citations: list[str] | None = None,
    accent_hex: str = "#4BB8E8",
    glow_hex: str = "#6366F1",
    logo_path: Path | None = None,
    fmt: Literal["pptx", "pdf"] = "pptx",
) -> tuple[bytes, str, str, DeckSpec]:
    """Return (file_bytes, mime_type, file_extension, deck_spec) for a Markdown source."""
    deck = markdown_to_deck(
        title,
        markdown,
        subtitle=subtitle,
        citations=citations,
        accent_hex=accent_hex,
        glow_hex=glow_hex,
    )
    if fmt == "pdf":
        return render_slides_pdf(deck, logo_path=logo_path), PDF_MIME, ".pdf", deck
    return render_pptx(deck, logo_path=logo_path), PPTX_MIME, ".pptx", deck


__all__ = ["PDF_MIME", "PPTX_MIME", "export_deck_bytes", "markdown_to_deck", "render_pptx", "render_slides_pdf"]
