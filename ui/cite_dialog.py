"""
Cite Dialog — APA/MLA/Chicago citation strings for TASS.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPlainTextEdit,
    QPushButton, QHBoxLayout, QTabWidget, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QGuiApplication


CITATIONS = {
    "APA": (
        "Doe, J., & Smith, A. (2026). TASS: Text Analysis for Social Scientists "
        "(Version 1.0.0) [Software]. SIM DAD LLC. https://doi.org/10.5281/zenodo.XXXXXXX"
    ),
    "MLA": (
        'Doe, Jane, and Alex Smith. TASS: Text Analysis for Social Scientists. '
        "Version 1.0.0, SIM DAD LLC, 2026, https://doi.org/10.5281/zenodo.XXXXXXX."
    ),
    "Chicago": (
        "Doe, Jane, and Alex Smith. 2026. TASS: Text Analysis for Social Scientists. "
        "Version 1.0.0. SIM DAD LLC. https://doi.org/10.5281/zenodo.XXXXXXX."
    ),
}


class CiteDialog(QDialog):
    """Shows copy-ready citation strings for TASS in APA, MLA, and Chicago formats."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How to Cite TASS")
        self.setMinimumWidth(540)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        intro = QLabel(
            "Please cite TASS in your publications. Select a format and copy the citation."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #555555;")
        layout.addWidget(intro)

        tabs = QTabWidget()
        for style, text in CITATIONS.items():
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            tab_layout.setContentsMargins(8, 8, 8, 8)

            edit = QPlainTextEdit(text)
            edit.setReadOnly(True)
            edit.setFixedHeight(80)
            tab_layout.addWidget(edit)

            copy_btn = QPushButton("Copy to Clipboard")
            copy_btn.clicked.connect(lambda _, t=text: self._copy(t))
            tab_layout.addWidget(copy_btn)

            tabs.addTab(tab, style)

        layout.addWidget(tabs)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _copy(self, text: str):
        QGuiApplication.clipboard().setText(text)
