"""
Settings Dialog — user preferences (color palette, default export path, etc.)
Sprint 9.
"""

from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFileDialog, QLineEdit, QFormLayout, QGroupBox,
    QFrame, QMessageBox,
)
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import QUrl
PALETTES = ["Default (ColorBrewer)", "Colorblind-Safe (viridis)", "Grayscale"]


class SettingsDialog(QDialog):
    """User preferences dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TASS Settings")
        self.setMinimumWidth(420)
        self.setModal(True)

        from services.settings_manager import SettingsManager
        self._settings = SettingsManager.instance()
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

        # Optional dictionaries group
        dict_group = QGroupBox("Optional Dictionaries")
        dict_layout = QVBoxLayout(dict_group)

        dict_note = QLabel(
            "These dictionaries use CC-BY-SA licenses and cannot be bundled with TASS. "
            "Download them separately and import via File → Import Dictionary."
        )
        dict_note.setWordWrap(True)
        dict_note.setFont(QFont("Segoe UI", 9))
        dict_note.setStyleSheet("color: #666666; margin-bottom: 8px;")
        dict_layout.addWidget(dict_note)

        from dictionaries.registry import BUILTIN_MANIFEST
        self._optional_dicts = [d for d in BUILTIN_MANIFEST if d.get("optional_download")]

        for entry in self._optional_dicts:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 4, 0, 4)

            info = QVBoxLayout()
            name_lbl = QLabel(f"<b>{entry['display_name']}</b>")
            name_lbl.setFont(QFont("Segoe UI", 9))
            info.addWidget(name_lbl)

            desc_lbl = QLabel(f"{entry['description']}  ({entry['license']})")
            desc_lbl.setFont(QFont("Segoe UI", 8))
            desc_lbl.setStyleSheet("color: #888888;")
            desc_lbl.setWordWrap(True)
            info.addWidget(desc_lbl)
            row_layout.addLayout(info, stretch=1)

            # Check if already installed
            builtin_dir = Path(__file__).parent.parent / "dictionaries" / "builtin"
            installed = (builtin_dir / entry["file"]).exists()

            if installed:
                status_lbl = QLabel("Installed")
                status_lbl.setFont(QFont("Segoe UI", 9))
                status_lbl.setStyleSheet("color: #16A34A; font-weight: bold;")
                row_layout.addWidget(status_lbl)
            else:
                link_btn = QPushButton("Download Info")
                link_btn.setFixedWidth(100)
                link_btn.setStyleSheet(
                    "QPushButton { background-color: #F5F5F5; color: #333333; "
                    "border: 1px solid #CCCCCC; border-radius: 4px; padding: 4px 8px; font-size: 11px; }"
                    "QPushButton:hover { background-color: #EEEEEE; }"
                )
                notice = entry.get("download_notice", "")
                link_btn.clicked.connect(lambda checked, n=notice, nm=entry["display_name"]: self._show_download_info(nm, n))
                row_layout.addWidget(link_btn)

            dict_layout.addWidget(row)

        layout.addWidget(dict_group)

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
        palette = self._settings.get("viz.palette", PALETTES[0])
        idx = self._palette_combo.findText(palette)
        if idx >= 0:
            self._palette_combo.setCurrentIndex(idx)

        export_path = self._settings.get("export.default_path", "")
        self._export_path_edit.setText(export_path)

    def _browse_export_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Default Export Folder")
        if path:
            self._export_path_edit.setText(path)

    def _show_download_info(self, name: str, notice: str):
        QMessageBox.information(self, f"Download {name}", notice)

    def _save_and_close(self):
        self._settings.set("viz.palette", self._palette_combo.currentText())
        self._settings.set("export.default_path", self._export_path_edit.text())

        from core.session import Session
        Session.instance().ui_state["color_palette"] = self._palette_combo.currentText()
        Session.instance().ui_state["export_path"] = self._export_path_edit.text()

        self.accept()
