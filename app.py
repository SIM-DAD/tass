"""
TASS Application bootstrap.
Handles: QApplication setup, global exception hook, NLTK data check,
license gate on startup, and main window launch.
"""

import sys
import os
import traceback

# Tell Windows this is its own app, not a Python child process.
# This makes the taskbar show TASS's icon instead of python.exe's icon.
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.simdadllc.tass")

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
        font = QFont("Segoe UI", 11)
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

        # Crash-reporting touchpoints (policy section 3): the first-launch
        # opt-in preference (A, shown once) and the post-crash review of any
        # queued reports (C). Both run after the license gate and before the
        # main window opens. Never fatal.
        try:
            from ui.crash_dialogs import FirstLaunchPrefDialog, PostRestartDialog
            FirstLaunchPrefDialog.maybe_show(self.main_window)
            PostRestartDialog.maybe_show(self.main_window)
        except Exception:
            pass

        self.main_window.show()

    # ------------------------------------------------------------------
    # Global exception handler
    # ------------------------------------------------------------------

    def _global_exception_handler(self, exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))

        # Manual-submit crash flow per the SIM DAD LLC error-reporting policy:
        # build a redacted, schema-fixed report, let the user review it in full,
        # and only ever send it via their own mail client on an explicit click.
        # If the user closes the dialog without choosing, the report is queued
        # locally for review on next launch (touchpoint C). Nothing is ever
        # transmitted automatically.
        try:
            from services import error_reporter as er
            from services.settings_manager import SettingsManager
            from ui.crash_dialogs import LiveCrashDialog, ACTION_CLOSED

            report = er.build_report(tb_str)
            settings = SettingsManager.instance()
            opted_in = settings.get(er.KEY_PROMPT_ON_CRASH, er.DEFAULT_PROMPT_ON_CRASH)

            dlg = LiveCrashDialog(report, opted_in=opted_in, parent=getattr(self, "main_window", None))
            dlg.exec()

            queue_on = settings.get(er.KEY_QUEUE_ON_CRASH, er.DEFAULT_QUEUE_ON_CRASH)
            if dlg.action == ACTION_CLOSED and queue_on:
                er.queue_report(report)
        except Exception:
            # The reporting subsystem must never raise from inside excepthook.
            # Best-effort: queue the redacted report locally so it is not lost.
            try:
                from services import error_reporter as er
                er.queue_report(er.build_report(tb_str))
            except Exception:
                pass
