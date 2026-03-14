#!/usr/bin/env python3
"""
Full release build script for TASS.

Steps:
  1. Run tests (pytest)
  2. Convert SVG icon → ICO
  3. Run PyInstaller (tass.spec)
  4. Run Inno Setup (installer.iss) — Windows only, requires iscc on PATH

Usage:
    python scripts/build.py [--skip-tests] [--skip-installer]
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], *, cwd: Path = ROOT) -> None:
    print(f"\n>>> {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        sys.exit(f"Step failed with code {result.returncode}: {cmd[0]}")


def main():
    parser = argparse.ArgumentParser(description="Build TASS release bundle.")
    parser.add_argument("--skip-tests",     action="store_true", help="Skip pytest step")
    parser.add_argument("--skip-installer", action="store_true", help="Skip Inno Setup step")
    args = parser.parse_args()

    # ── Step 1: Tests ──────────────────────────────────────────────────
    if not args.skip_tests:
        print("\n=== Step 1: Running test suite ===")
        run([sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"])

    # ── Step 2: Check icon ────────────────────────────────────────────
    ico_path = ROOT / "assets" / "icons" / "tass_icon.ico"
    if not ico_path.exists():
        print("\n=== Step 2: WARNING — tass_icon.ico not found ===")
        print("  Place the Illustrator-exported tass_icon.ico in assets/icons/ before building.")
        sys.exit("Build stopped: missing tass_icon.ico")
    else:
        print(f"\n=== Step 2: Icon found ({ico_path.name}) ===")

    # ── Step 3: PyInstaller ───────────────────────────────────────────
    print("\n=== Step 3: Running PyInstaller ===")
    run([sys.executable, "-m", "PyInstaller", "tass.spec", "--clean", "--noconfirm"])

    dist_exe = ROOT / "dist" / "TASS" / "TASS.exe"
    if not dist_exe.exists():
        sys.exit(f"PyInstaller output not found: {dist_exe}")
    print(f"Built: {dist_exe}  ({dist_exe.stat().st_size / 1e6:.1f} MB)")

    # ── Step 4: Inno Setup ────────────────────────────────────────────
    if not args.skip_installer and sys.platform == "win32":
        print("\n=== Step 4: Running Inno Setup ===")
        # Ensure output directory exists
        (ROOT / "installer").mkdir(exist_ok=True)

        # Try common iscc locations
        iscc_candidates = [
            Path(r"C:\Program Files (x86)\Inno Setup 6\iscc.exe"),
            Path(r"C:\Program Files\Inno Setup 6\iscc.exe"),
            Path("iscc"),   # on PATH
        ]
        iscc = next((p for p in iscc_candidates if Path(p).exists()), None)
        if iscc is None:
            print(
                "  WARNING: iscc.exe not found. Install Inno Setup 6 from "
                "https://jrsoftware.org/isinfo.php and re-run with iscc on PATH."
            )
        else:
            run([str(iscc), "installer.iss"])
            installer_dir = ROOT / "installer"
            installers = list(installer_dir.glob("TASS-Setup-*.exe"))
            if installers:
                inst = max(installers, key=lambda p: p.stat().st_mtime)
                print(f"Installer: {inst}  ({inst.stat().st_size / 1e6:.1f} MB)")
    elif args.skip_installer:
        print("\n=== Step 4: Inno Setup skipped (--skip-installer) ===")
    else:
        print("\n=== Step 4: Inno Setup skipped (not Windows) ===")

    print("\n✓ Build complete.")


if __name__ == "__main__":
    main()
