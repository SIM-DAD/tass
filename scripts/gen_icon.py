#!/usr/bin/env python3
"""
Render assets/icons/logo.svg → assets/icons/tass_icon.ico
Uses PySide6 (no cairosvg / GTK required).

Usage:
    python scripts/gen_icon.py
"""
import sys
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "assets" / "icons" / "logo.svg"
ICO_PATH = ROOT / "assets" / "icons" / "tass_icon.ico"
SIZES = [16, 32, 48, 64, 128, 256]


def main():
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow not found:  pip install Pillow")

    # Bootstrap a minimal QApplication so QSvgRenderer works
    from PySide6.QtWidgets import QApplication
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtCore import Qt, QRectF

    app = QApplication.instance() or QApplication(sys.argv)

    if not SVG_PATH.exists():
        sys.exit(f"SVG not found: {SVG_PATH}")

    # Qt's SVG renderer doesn't support CSS class-based fills.
    # Pre-process: inline the fill colors from the <style> block.
    import re
    svg_text = SVG_PATH.read_text(encoding="utf-8")
    # Extract class→fill mappings from <style> block
    style_fills = dict(re.findall(r'\.(st\d+)\s*\{\s*fill:\s*(#[0-9a-fA-F]+)', svg_text))
    for cls, color in style_fills.items():
        svg_text = re.sub(rf'class="{cls}"', f'fill="{color}"', svg_text)
    svg_text = re.sub(r'<style>.*?</style>', '', svg_text, flags=re.DOTALL)
    svg_bytes = svg_text.encode("utf-8")

    from PySide6.QtCore import QByteArray
    renderer = QSvgRenderer(QByteArray(svg_bytes))
    if not renderer.isValid():
        sys.exit(f"Invalid SVG: {SVG_PATH}")

    import tempfile, os

    # Render at 256×256 (highest quality); Pillow downsamples to all sizes
    vb = renderer.viewBoxF()
    aspect = vb.width() / vb.height()
    BIG = 256
    w = BIG * 0.9
    h = w / aspect
    x = (BIG - w) / 2
    y = (BIG - h) / 2

    img = QImage(BIG, BIG, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    renderer.render(painter, QRectF(x, y, w, h))
    painter.end()

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()
    img.save(tmp.name, "PNG")
    pil = Image.open(tmp.name).copy()
    os.unlink(tmp.name)
    print(f"  rendered 256x256 source, generating sizes: {SIZES}")

    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    pil.save(
        ICO_PATH,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
    )
    print(f"Written  {ICO_PATH}  ({ICO_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
