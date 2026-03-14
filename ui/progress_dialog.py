"""
Progress Dialog — modal with progress bar, live status, and cancel button.
Used during analysis runs.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QHBoxLayout,
)
from PySide6.QtCore import Qt, Signal


class ProgressDialog(QDialog):
    """Modal progress dialog for long-running analysis operations."""

    cancel_requested = Signal()

    def __init__(self, title: str = "Running Analysis…", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowCloseButtonHint
        )
        self._build_ui()
        self._cancelled = False

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        self._title_lbl = QLabel("Running Analysis…")
        self._title_lbl.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(self._title_lbl)

        self._status_lbl = QLabel("Initializing…")
        self._status_lbl.setStyleSheet("color: #555555;")
        layout.addWidget(self._status_lbl)

        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setTextVisible(True)
        layout.addWidget(self._progress)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #DC2626; "
            "border: 1px solid #DC2626; border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:hover { background-color: #FEF2F2; }"
        )
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Public API (connected to worker signals)
    # ------------------------------------------------------------------

    def update_progress(self, done: int, total: int, message: str = ""):
        if total > 0:
            pct = int(done / total * 100)
            self._progress.setValue(pct)
            self._progress.setFormat(f"{pct}%  ({done:,} / {total:,})")
        if message:
            self._status_lbl.setText(message)

    def set_indeterminate(self, message: str = ""):
        self._progress.setMaximum(0)  # indeterminate spinner
        if message:
            self._status_lbl.setText(message)

    def finish(self):
        self._progress.setValue(self._progress.maximum() or 100)
        self._cancel_btn.setEnabled(False)
        self.accept()

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def _on_cancel(self):
        self._cancelled = True
        self._cancel_btn.setEnabled(False)
        self._status_lbl.setText("Cancelling…")
        self.cancel_requested.emit()
