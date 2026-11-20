"""Generate a crisp light-surface Retina macOS DMG drag-to-Applications background."""

import importlib
import sys
from pathlib import Path
from typing import Any

WIDTH = 660
HEIGHT = 460


def _color(appkit: Any, r: float, g: float, b: float, a: float = 1.0) -> Any:
    return appkit.NSColor.colorWithSRGBRed_green_blue_alpha_(r / 255.0, g / 255.0, b / 255.0, a)


def _draw_centered_text(appkit: Any, text: str, y: float, size: float, weight: float, color: Any) -> None:
    font = appkit.NSFont.systemFontOfSize_weight_(size, weight)
    attrs = {appkit.NSFontAttributeName: font, appkit.NSForegroundColorAttributeName: color}
    ns_text = appkit.NSAttributedString.alloc().initWithString_attributes_(text, attrs)
    text_size = ns_text.size()
    ns_text.drawAtPoint_(((WIDTH - text_size.width) / 2.0, y))


def render_background(output_path: Path, scale: int = 1) -> None:
    """Render a light-surface 1x/2x PNG so macOS Finder's black icon labels stay crisp."""
    appkit: Any = importlib.import_module("AppKit")
    px_w, px_h = WIDTH * scale, HEIGHT * scale
    rep = appkit.NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, px_w, px_h, 8, 4, True, False, appkit.NSCalibratedRGBColorSpace, 0, 0
    )
    rep.setSize_((WIDTH, HEIGHT))
    ctx = appkit.NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    appkit.NSGraphicsContext.saveGraphicsState()
    appkit.NSGraphicsContext.setCurrentContext_(ctx)

    # Clean light canvas (#F4F7FB) so Finder's forced-black labels have high contrast
    _color(appkit, 244, 247, 251).setFill()
    appkit.NSBezierPath.fillRect_(((0, 0), (WIDTH, HEIGHT)))

    # Subtle top accent bar matching REALM brand (#4BB8E8)
    _color(appkit, 75, 184, 232).setFill()
    appkit.NSBezierPath.fillRect_(((0, HEIGHT - 4), (WIDTH, 4)))

    # Elevated white drop-zone card safely inside top 350pt (never clipped by Finder bars)
    card = appkit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(((44, HEIGHT - 282), (WIDTH - 88, 208)), 18, 18)
    _color(appkit, 255, 255, 255).setFill()
    card.fill()
    _color(appkit, 214, 226, 240).setStroke()
    card.setLineWidth_(1.25)
    card.stroke()

    # Crisp left-to-right arrow aligned with icon centers (Finder y=168 -> AppKit y=HEIGHT-168)
    cy = HEIGHT - 168
    arrow = appkit.NSBezierPath.bezierPath()
    arrow.setLineWidth_(3.0)
    arrow.setLineCapStyle_(appkit.NSLineCapStyleRound)
    arrow.setLineJoinStyle_(appkit.NSLineJoinStyleRound)
    arrow.moveToPoint_((294, cy))
    arrow.lineToPoint_((366, cy))
    arrow.moveToPoint_((352, cy + 12))
    arrow.lineToPoint_((366, cy))
    arrow.lineToPoint_((352, cy - 12))
    _color(appkit, 34, 152, 209).setStroke()
    arrow.stroke()

    # Crisp dark-slate typography safely above y=350pt
    _draw_centered_text(appkit, "Install REALM Engine", HEIGHT - 52, 19.0, appkit.NSFontWeightSemibold, _color(appkit, 11, 16, 32))
    _draw_centered_text(appkit, "Drag REALM Engine into Applications", HEIGHT - 318, 13.0, appkit.NSFontWeightMedium, _color(appkit, 71, 85, 105))

    appkit.NSGraphicsContext.restoreGraphicsState()
    png_data = rep.representationUsingType_properties_(appkit.NSBitmapImageFileTypePNG, {})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    png_data.writeToFile_atomically_(str(output_path), True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: make_dmg_background.py <output.png>")
    out = Path(sys.argv[1])
    render_background(out, scale=1)
    render_background(out.with_name(f"{out.stem}@2x{out.suffix}"), scale=2)


if __name__ == "__main__":
    main()
