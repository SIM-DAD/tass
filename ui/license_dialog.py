"""
TASS License Dialog — trial signup and license key activation.
mode: "trial_signup" | "activate" | "expired"
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QWidget, QMessageBox, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class LicenseDialog(QDialog):
    """
    Handles three scenarios in one dialog:
    - trial_signup: first launch, no license cache
    - activate: user opens from menu to enter/change a key
    - expired: trial has run out; prompt to purchase or re-enter key
    """

    def __init__(self, mode: str = "trial_signup", parent=None):
        super().__init__(parent)
        self.mode = mode
        self.setWindowTitle("TASS — Activate or Start Trial")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # Header
        header = QLabel("Activate TASS")
        header_font = QFont("Segoe UI", 16)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)

        if self.mode == "expired":
            banner = QLabel("⚠  Your trial has expired. TASS is now in view-only mode.")
            banner.setWordWrap(True)
            banner.setStyleSheet(
                "background-color: #FEF2F2; color: #DC2626; border: 1px solid #FECACA; "
                "border-radius: 6px; padding: 10px;"
            )
            layout.addWidget(banner)

        # Tabs: Trial / License Key
        tabs = QTabWidget()

        # -- Trial tab --
        trial_tab = QWidget()
        trial_layout = QVBoxLayout(trial_tab)
        trial_layout.setSpacing(12)

        trial_layout.addWidget(QLabel(
            "Start a free 14-day trial (up to 500 rows per analysis).\n"
            "Enter your email to begin:"
        ))

        self._email_edit = QLineEdit()
        self._email_edit.setPlaceholderText("you@institution.edu")
        trial_layout.addWidget(self._email_edit)

        start_btn = QPushButton("Start Free Trial")
        start_btn.setFixedHeight(40)
        start_btn.clicked.connect(self._start_trial)
        trial_layout.addWidget(start_btn)

        trial_layout.addStretch()
        tabs.addTab(trial_tab, "Free Trial")

        # -- License Key tab --
        key_tab = QWidget()
        key_layout = QVBoxLayout(key_tab)
        key_layout.setSpacing(12)

        key_layout.addWidget(QLabel(
            "Enter your Lemon Squeezy license key to activate TASS.\n"
            "Keys are delivered via email after purchase."
        ))

        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("XXXX-XXXX-XXXX-XXXX")
        self._key_edit.setFont(QFont("Courier New", 11))
        key_layout.addWidget(self._key_edit)

        activate_btn = QPushButton("Activate License")
        activate_btn.setFixedHeight(40)
        activate_btn.clicked.connect(self._activate_license)
        key_layout.addWidget(activate_btn)

        purchase_sep = QFrame()
        purchase_sep.setFrameShape(QFrame.HLine)
        purchase_sep.setStyleSheet("background-color: #EEEEEE;")
        key_layout.addWidget(purchase_sep)

        purchase_lbl = QLabel(
            "Don't have a license? <a href='https://tass.simdad.com/buy' "
            "style='color:#2563EB;'>Purchase TASS →</a>"
        )
        purchase_lbl.setOpenExternalLinks(True)
        purchase_lbl.setStyleSheet("font-size: 9pt; color: #555555;")
        key_layout.addWidget(purchase_lbl)

        key_layout.addStretch()
        tabs.addTab(key_tab, "License Key")

        # Start on license tab if coming from expired or activate mode
        if self.mode in ("expired", "activate"):
            tabs.setCurrentIndex(1)

        layout.addWidget(tabs)

        # Cancel button
        cancel_layout = QHBoxLayout()
        cancel_layout.addStretch()
        cancel_btn = QPushButton("Continue in View-Only Mode" if self.mode == "expired" else "Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #555555; "
            "border: 1px solid #CCCCCC; border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:hover { background-color: #F5F5F5; }"
        )
        cancel_btn.clicked.connect(self.reject)
        cancel_layout.addWidget(cancel_btn)
        layout.addLayout(cancel_layout)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _start_trial(self):
        email = self._email_edit.text().strip()
        if "@" not in email or "." not in email:
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return

        try:
            from services.license import LicenseService
            LicenseService().start_trial(email)
            QMessageBox.information(
                self,
                "Trial Started",
                f"Your 14-day trial has started.\n\nEmail: {email}\n\n"
                "You can analyze up to 500 rows per run during your trial.",
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not start trial:\n{exc}")

    def _activate_license(self):
        key = self._key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "No Key", "Please enter your license key.")
            return

        try:
            from services.license import LicenseService
            status = LicenseService().activate_license(key)
            QMessageBox.information(
                self,
                "License Activated",
                f"TASS is now activated.\n\nTier: {status.tier or 'Individual'}\n"
                f"Expires: {status.expires_at or 'N/A'}",
            )
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Activation Failed", str(exc))
