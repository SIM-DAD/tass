"""
TASS — Text Analysis for Social Scientists
Entry point.
"""

import sys
import os

# Ensure the app directory is on the path (needed when running from PyInstaller bundle)
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

# Load .env in development (no-op in PyInstaller bundle where .env won't exist)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass  # python-dotenv not installed; rely on system environment variables

from PySide6.QtWidgets import QApplication
from app import TASSApp


def main():
    # Qt 6 enables high-DPI scaling automatically; no setAttribute needed.
    app = TASSApp(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
