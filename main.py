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

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from app import TASSApp


def main():
    # Enable high-DPI scaling (PySide6 handles this automatically in Qt 6)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = TASSApp(sys.argv)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
