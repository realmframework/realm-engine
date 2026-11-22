"""Shared cross-platform Unicode TTF font discovery, RGB helpers, and logo drawing for PDF/PPTX."""

from __future__ import annotations

import os
from pathlib import Path

from fpdf import FPDF

_WIN_FONTS = Path(os.environ.get("WINDIR") or os.environ.get("SYSTEMROOT") or "C:/Windows") / "Fonts"
_FONT_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    str(_WIN_FONTS / "arial.ttf"),
)
_BOLD_CANDIDATES = (
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    str(_WIN_FONTS / "arialbd.ttf"),
)


def _find_font(paths: tuple[str, ...]) -> Path | None:
    return next((Path(p) for p in paths if Path(p).is_file()), None)


def setup_pdf_unicode_font(pdf: FPDF, family_name: str = "RealmSans") -> tuple[str, bool]:
    """Register a cross-platform Unicode TTF font pair on pdf, falling back cleanly to Helvetica."""
    regular, bold = _find_font(_FONT_CANDIDATES), _find_font(_BOLD_CANDIDATES)
    if regular is not None:
        try:
            pdf.add_font(family_name, "", str(regular))
            pdf.add_font(family_name, "B", str(bold or regular))
            return family_name, True
        except (RuntimeError, OSError, ValueError):
            pass
    return "Helvetica", False


def pdf_encode(text: str, uni: bool) -> str:
    """Encode text safely for either Unicode TTF or Latin-1 Helvetica fallback."""
    if uni:
        return text
    cleaned = text.replace("—", "-").replace("–", "-").replace("•", "-").replace("€", "EUR ")
    return cleaned.encode("latin-1", errors="replace").decode("latin-1")


def hex_to_rgb(hex_color: str, fallback: str = "#4BB8E8") -> tuple[int, int, int]:
    """Convert a #RRGGBB color string to an (R, G, B) integer tuple."""
    clean = (hex_color or "").strip().lstrip("#")
    if len(clean) != 6:
        clean = fallback.lstrip("#")
    try:
        return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
    except ValueError:
        fb = fallback.lstrip("#")
        return (int(fb[0:2], 16), int(fb[2:4], 16), int(fb[4:6], 16))


def draw_pdf_logo(pdf: FPDF, logo_path: Path | None, x: float, y: float, h: float) -> bool:
    """Render an optional workspace logo image into a PDF, returning True if drawn."""
    if logo_path and logo_path.is_file() and logo_path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        try:
            pdf.image(str(logo_path), x=x, y=y, h=h)
            return True
        except (RuntimeError, OSError, ValueError):
            return False
    return False
