#!/usr/bin/env python3
"""
Convert assets/icons/app-icon.svg → assets/icons/tass.ico
Produces a multi-size ICO (16, 32, 48, 64, 128, 256 px) required by PyInstaller
and the Windows shell.

Requirements:
    pip install cairosvg Pillow

Usage:
    python scripts/build_icon.py
"""

import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_PATH = ROOT / "assets" / "icons" / "app-icon.svg"
ICO_PATH = ROOT / "assets" / "icons" / "tass.ico"

SIZES = [16, 32, 48, 64, 128, 256]


def build_icon():
    try:
        import cairosvg
    except ImportError:
        sys.exit(
            "cairosvg not found. Install it with:\n"
            "    pip install cairosvg Pillow\n"
            "On Windows you may also need the GTK runtime from:\n"
            "    https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer"
        )

    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow not found. Install it with:  pip install Pillow")

    if not SVG_PATH.exists():
        sys.exit(f"SVG not found: {SVG_PATH}")

    print(f"Reading  {SVG_PATH}")
    svg_data = SVG_PATH.read_bytes()

    frames: list[Image.Image] = []
    for size in SIZES:
        png_data = cairosvg.svg2png(
            bytestring=svg_data,
            output_width=size,
            output_height=size,
        )
        img = Image.open(io.BytesIO(png_data)).convert("RGBA")
        frames.append(img)
        print(f"  rendered {size}x{size}")

    ICO_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Save as ICO with all sizes embedded
    frames[0].save(
        ICO_PATH,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=frames[1:],
    )
    print(f"Written  {ICO_PATH}  ({ICO_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build_icon()
