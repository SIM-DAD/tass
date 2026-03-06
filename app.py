"""
TASS Application bootstrap.
Handles: QApplication setup, global exception hook, NLTK data check,
license gate on startup, and main window launch.
"""

import sys
import os
import traceback

from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap, QColor

TASS_VERSION = "1.0.0"
APP_NAME = "TASS"
ORG_NAME = "SIM DAD LLC"


class TASSApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self.setApplicationName(APP_NAME)
        self.setApplicationVersion(TASS_VERSION)
        self.setOrganizationName(ORG_NAME)

        # Apply stylesheet
        self._apply_stylesheet()

        # Set default font
        font = QFont("Segoe UI", 10)
        self.setFont(font)

        # Install global exception handler
        sys.excepthook = self._global_exception_handler

        # Ensure NLTK data is available
        self._ensure_nltk_data()

        # Show splash and launch main window
        self._launch()

    # ------------------------------------------------------------------
    # Stylesheet
    # ------------------------------------------------------------------

    def _apply_stylesheet(self):
        style_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "assets", "styles", "theme.qss",
        )
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as fh:
                self.setStyleSheet(fh.read())

    # ------------------------------------------------------------------
    # NLTK bootstrap
    # ------------------------------------------------------------------

    def _ensure_nltk_data(self):
        """Download required NLTK corpora if not already present."""
        try:
            import nltk
            required = [
                ("tokenizers/punkt", "punkt"),
                ("tokenizers/punkt_tab", "punkt_tab"),
                ("corpora/stopwords", "stopwords"),
                ("corpora/wordnet", "wordnet"),
                ("taggers/averaged_perceptron_tagger", "averaged_perceptron_tagger"),
            ]
            for path, package in required:
                try:
                    nltk.data.find(path)
                except LookupError:
                    nltk.download(package, quiet=True)
        except Exception:
            pass  # NLTK issues are non-fatal at startup; engine will surface errors later

    # ------------------------------------------------------------------
    # Launch sequence
    # ------------------------------------------------------------------

    def _launch(self):
        from ui.main_window import MainWindow
        from services.license import LicenseService

        self.main_window = MainWindow()

        # Check license / trial status
        license_svc = LicenseService()
        status = license_svc.get_status()
        self.main_window.set_license_status(status.display_label)

        if status.mode == "expired":
            from ui.license_dialog import LicenseDialog
            dlg = LicenseDialog(mode="expired", parent=self.main_window)
            dlg.exec()
        elif status.mode == "none":
            from ui.license_dialog import LicenseDialog
            dlg = LicenseDialog(mode="trial_signup", parent=self.main_window)
            dlg.exec()

        self.main_window.show()

    # ------------------------------------------------------------------
    # Global exception handler
    # ------------------------------------------------------------------

    def _global_exception_handler(self, exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        # Show user-facing dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("TASS — Unexpected Error")
        msg.setText("An unexpected error occurred.")
        msg.setInformativeText(
            "Would you like to send a crash report to help improve TASS?\n\n"
            "No personal data or text content is ever included."
        )
        msg.setDetailedText(tb_str)
        msg.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No
        )
        msg.button(QMessageBox.Yes).setText("Send Report")
        msg.button(QMessageBox.No).setText("Don't Send")

        result = msg.exec()

        if result == QMessageBox.Yes:
            try:
                from services.error_reporter import ErrorReporter
                ErrorReporter().send(tb_str)
            except Exception:
                pass
