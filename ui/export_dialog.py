"""
Export Dialog — Sprint 7.
Format checkboxes (CSV, Excel, PNG, SVG), output directory picker, run button.
Appends citation block to all text-based exports.
"""

from __future__ import annotations
import os
from typing import Optional

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QLineEdit, QFileDialog, QGroupBox, QMessageBox,
    QProgressBar, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ExportDialog(QDialog):
    """Export results in one or more formats to a chosen output directory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export Results")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build_ui()
        self._load_defaults()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        hdr = QLabel("Export Analysis Results")
        hdr.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(hdr)

        sub = QLabel(
            "Choose output formats and destination folder.\n"
            "A TASS citation block is automatically appended to all text-based exports."
        )
        sub.setStyleSheet("color: #6B7280; font-size: 9pt;")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E5E7EB;")
        layout.addWidget(sep)

        # ── Format selection ─────────────────────────────────────────
        fmt_box = QGroupBox("Output Formats")
        fmt_box.setFont(QFont("Segoe UI", 9, QFont.Bold))
        fmt_layout = QVBoxLayout(fmt_box)
        fmt_layout.setSpacing(8)

        self.cb_csv = QCheckBox("CSV  —  Entry-level scores (one row per text entry)")
        self.cb_csv.setChecked(True)
        fmt_layout.addWidget(self.cb_csv)

        self.cb_excel = QCheckBox(
            "Excel (.xlsx)  —  Multi-sheet workbook (scores, summary, group comparisons, citation)"
        )
        self.cb_excel.setChecked(True)
        fmt_layout.addWidget(self.cb_excel)

        self.cb_png = QCheckBox("PNG charts  —  300 DPI publication-quality images")
        self.cb_png.setChecked(False)
        fmt_layout.addWidget(self.cb_png)

        self.cb_svg = QCheckBox("SVG charts  —  Vector format for journal submission")
        self.cb_svg.setChecked(False)
        fmt_layout.addWidget(self.cb_svg)

        layout.addWidget(fmt_box)

        # ── Output directory ─────────────────────────────────────────
        dir_box = QGroupBox("Output Directory")
        dir_box.setFont(QFont("Segoe UI", 9, QFont.Bold))
        dir_layout = QHBoxLayout(dir_box)

        self.dir_edit = QLineEdit()
        self.dir_edit.setPlaceholderText("Choose a folder…")
        self.dir_edit.setReadOnly(False)
        dir_layout.addWidget(self.dir_edit, 1)

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self._browse_dir)
        dir_layout.addWidget(browse_btn)

        layout.addWidget(dir_box)

        # ── Progress bar ─────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(6)
        self._progress.setStyleSheet(
            "QProgressBar { border: none; background-color: #E5E7EB; border-radius: 3px; }"
            "QProgressBar::chunk { background-color: #2563EB; border-radius: 3px; }"
        )
        self._progress.hide()
        layout.addWidget(self._progress)

        # ── Buttons ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #374151; "
            "border: 1px solid #D1D5DB; border-radius: 6px; padding: 8px 20px; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.setDefault(True)
        self.export_btn.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: white; "
            "border-radius: 6px; padding: 8px 24px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1D4ED8; }"
            "QPushButton:disabled { background-color: #93C5FD; }"
        )
        self.export_btn.clicked.connect(self._run_export)
        btn_row.addWidget(self.export_btn)

        layout.addLayout(btn_row)

    def _load_defaults(self):
        from core.session import Session
        default_dir = Session.instance().ui_state.get("export_path", "")
        if not default_dir:
            default_dir = os.path.expanduser("~")
        self.dir_edit.setText(default_dir)

    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.dir_edit.text()
        )
        if path:
            self.dir_edit.setText(path)

    def _run_export(self):
        from core.session import Session
        from core.statistics_engine import StatisticsEngine
        from core.export_engine import ExportEngine

        session = Session.instance()

        if not session.has_results:
            QMessageBox.information(self, "No Results", "Run an analysis before exporting.")
            return

        out_dir = self.dir_edit.text().strip()
        if not out_dir or not os.path.isdir(out_dir):
            QMessageBox.warning(self, "Invalid Directory",
                                "Please choose a valid output directory.")
            return

        formats = {
            "csv":   self.cb_csv.isChecked(),
            "excel": self.cb_excel.isChecked(),
            "png":   self.cb_png.isChecked(),
            "svg":   self.cb_svg.isChecked(),
        }
        if not any(formats.values()):
            QMessageBox.warning(self, "No Format", "Select at least one output format.")
            return

        # Save preferred export path
        session.ui_state["export_path"] = out_dir

        self.export_btn.setEnabled(False)
        self._progress.show()
        exported: list = []
        errors: list = []
        steps = sum(formats.values())
        step = 0

        engine = ExportEngine(out_dir)
        stats_eng = StatisticsEngine()

        try:
            results = session.results
            scores = results.entry_scores
            raw = session.raw_df
            meta_cols = session.column_mapping.metadata_columns

            summary = stats_eng.document_summary(scores)

            group_stats_df = None
            if results.group_stats:
                rows = [gs.to_dict() for gs in results.group_stats.values()]
                import pandas as pd
                group_stats_df = pd.DataFrame(rows)

            if formats["csv"]:
                try:
                    path = engine.export_csv(scores, raw, metadata_columns=meta_cols)
                    exported.append(path)
                except Exception as e:
                    errors.append(f"CSV: {e}")
                step += 1
                self._progress.setValue(int(step / steps * 100))

            if formats["excel"]:
                try:
                    path = engine.export_excel(
                        scores, summary, group_stats_df, raw,
                        metadata_columns=meta_cols
                    )
                    exported.append(path)
                except Exception as e:
                    errors.append(f"Excel: {e}")
                step += 1
                self._progress.setValue(int(step / steps * 100))

            if formats["png"] or formats["svg"]:
                try:
                    from core.visualization_engine import VisualizationEngine
                    viz = VisualizationEngine(
                        palette=session.ui_state.get("color_palette", "default")
                    )
                    bar_fig = viz.bar_chart(summary)
                    for fmt, flag in [("png", formats["png"]), ("svg", formats["svg"])]:
                        if flag:
                            paths = engine.export_figure(bar_fig, f"bar_chart.{fmt}")
                            exported.extend(paths)
                    import matplotlib.pyplot as plt
                    plt.close(bar_fig)
                except Exception as e:
                    errors.append(f"Charts: {e}")
                step += 1
                self._progress.setValue(100)

        finally:
            self.export_btn.setEnabled(True)
            self._progress.hide()

        if errors:
            msg = "Export completed with errors:\n" + "\n".join(errors)
            if exported:
                msg += f"\n\nSuccessfully exported {len(exported)} file(s)."
            QMessageBox.warning(self, "Export Warnings", msg)
        else:
            msg = f"Exported {len(exported)} file(s) to:\n{out_dir}"
            QMessageBox.information(self, "Export Complete", msg)
            self.accept()
