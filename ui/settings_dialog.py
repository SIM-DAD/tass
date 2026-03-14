"""
Settings Dialog — user preferences (color palette, default export path, etc.)
Sprint 9.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QLineEdit, QFormLayout, QGroupBox,
)
from PySide6.QtCore import QSettings


PALETTES = ["Default (ColorBrewer)", "Colorblind-Safe (viridis)", "Grayscale"]


class SettingsDialog(QDialog):
    """User preferences dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TASS Settings")
        self.setMinimumWidth(420)
        self.setModal(True)

        self._settings = QSettings("SIM DAD LLC", "TASS")
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(20)

        # Visualization group
        viz_group = QGroupBox("Visualization")
        viz_form = QFormLayout(viz_group)

        self._palette_combo = QComboBox()
        self._palette_combo.addItems(PALETTES)
        viz_form.addRow("Color Palette:", self._palette_combo)

        layout.addWidget(viz_group)

        # Export group
        export_group = QGroupBox("Export")
        export_form = QFormLayout(export_group)

        export_path_row = QHBoxLayout()
        self._export_path_edit = QLineEdit()
        self._export_path_edit.setPlaceholderText("Default output folder…")
        export_path_row.addWidget(self._export_path_edit)

        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(80)
        browse_btn.setStyleSheet(
            "QPushButton { background-color: #F5F5F5; color: #333333; "
            "border: 1px solid #CCCCCC; border-radius: 4px; padding: 5px 8px; }"
            "QPushButton:hover { background-color: #EEEEEE; }"
        )
        browse_btn.clicked.connect(self._browse_export_path)
        export_path_row.addWidget(browse_btn)

        export_form.addRow("Default Export Path:", export_path_row)
        layout.addWidget(export_group)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #555555; "
            "border: 1px solid #CCCCCC; border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:hover { background-color: #F5F5F5; }"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_and_close)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _load_settings(self):
        palette = self._settings.value("viz/palette", PALETTES[0])
        idx = self._palette_combo.findText(palette)
        if idx >= 0:
            self._palette_combo.setCurrentIndex(idx)

        export_path = self._settings.value("export/default_path", "")
        self._export_path_edit.setText(export_path)

    def _browse_export_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Default Export Folder")
        if path:
            self._export_path_edit.setText(path)

    def _save_and_close(self):
        self._settings.setValue("viz/palette", self._palette_combo.currentText())
        self._settings.setValue("export/default_path", self._export_path_edit.text())

        from core.session import Session
        Session.instance().ui_state["color_palette"] = self._palette_combo.currentText()
        Session.instance().ui_state["export_path"] = self._export_path_edit.text()

        self.accept()
