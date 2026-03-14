"""
Compare Panel — Sprint 5.
Group definition UI + statistical comparison results.
Runs StatisticsWorker in background; displays results table and inline charts.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QSizePolicy, QGroupBox, QCheckBox, QSplitter,
    QMessageBox, QAbstractItemView, QProgressBar,
)
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont, QColor

import pandas as pd


# ── Significance star labels ─────────────────────────────────────────
def _sig_label(p: Optional[float]) -> str:
    if p is None:
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "n.s."


def _sig_color(p: Optional[float]) -> Optional[QColor]:
    if p is None:
        return None
    if p < 0.05:
        return QColor("#D1FAE5")   # green tint
    return QColor("#FEF9C3")       # yellow tint


# ══════════════════════════════════════════════════════════════════════
# Group Config Panel (top)
# ══════════════════════════════════════════════════════════════════════

class _GroupConfigPanel(QFrame):
    """Controls for selecting group column and running comparison."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        self.setFixedHeight(80)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(16)

        # Group column selector
        lbl_col = QLabel("Group column:")
        lbl_col.setFont(QFont("Segoe UI", 9))
        layout.addWidget(lbl_col)

        self.group_col_combo = QComboBox()
        self.group_col_combo.setMinimumWidth(160)
        self.group_col_combo.setToolTip(
            "Select the column whose values define the groups to compare."
        )
        layout.addWidget(self.group_col_combo)

        # Options
        self.nonparametric_cb = QCheckBox("Non-parametric (Mann-Whitney U)")
        self.nonparametric_cb.setFont(QFont("Segoe UI", 9))
        self.nonparametric_cb.setToolTip(
            "When checked: Mann-Whitney U (2 groups) instead of Welch t-test. "
            "Bonferroni correction always applied across categories."
        )
        layout.addWidget(self.nonparametric_cb)

        self.bonferroni_cb = QCheckBox("Bonferroni correction")
        self.bonferroni_cb.setFont(QFont("Segoe UI", 9))
        self.bonferroni_cb.setChecked(True)
        self.bonferroni_cb.setToolTip(
            "Apply Bonferroni correction for multiple comparisons across dictionary categories."
        )
        layout.addWidget(self.bonferroni_cb)

        layout.addStretch()

        self.run_btn = QPushButton("Run Comparison")
        self.run_btn.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: white; "
            "border-radius: 6px; padding: 8px 20px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1D4ED8; }"
            "QPushButton:disabled { background-color: #93C5FD; }"
        )
        layout.addWidget(self.run_btn)

    def populate_columns(self, columns: List[str]):
        self.group_col_combo.clear()
        for col in columns:
            self.group_col_combo.addItem(col)

    @property
    def selected_group_column(self) -> Optional[str]:
        return self.group_col_combo.currentText() or None


# ══════════════════════════════════════════════════════════════════════
# Results Table
# ══════════════════════════════════════════════════════════════════════

class _ResultsTable(QTableWidget):
    """
    Displays group comparison results.
    Columns: Category | Groups (mean±SD each) | Test | Statistic | p | Sig | Effect size
    """

    COL_CATEGORY = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.setFont(QFont("Segoe UI", 9))

    def load(self, group_stats: Dict, group_names: List[str]):
        """Populate from dict of {col: GroupStats}."""
        # Build column headers
        fixed_cols = ["Category", "Test", "Statistic", "p-value", "Sig.", "Effect Size", "Effect Type"]
        group_desc_cols = [f"{g}: mean (SD)" for g in group_names]
        all_cols = fixed_cols[:1] + group_desc_cols + fixed_cols[1:]

        self.setColumnCount(len(all_cols))
        self.setHorizontalHeaderLabels(all_cols)
        self.setRowCount(len(group_stats))

        for row, (col_key, gs) in enumerate(sorted(group_stats.items())):
            cat_display = col_key.split("__")[-1] if "__" in col_key else col_key
            dict_name = col_key.split("__")[0] if "__" in col_key else ""

            c = 0
            # Category
            item = QTableWidgetItem(cat_display)
            item.setToolTip(f"{dict_name}: {col_key}")
            self.setItem(row, c, item)
            c += 1

            # Group means
            for g in group_names:
                desc = gs.group_descriptives.get(str(g), {})
                mean = desc.get("mean")
                sd = desc.get("std")
                val = f"{mean:.3f} ({sd:.3f})" if mean is not None and sd is not None else "—"
                self.setItem(row, c, QTableWidgetItem(val))
                c += 1

            # Test name
            self.setItem(row, c, QTableWidgetItem(gs.test_name or "—"))
            c += 1

            # Statistic
            stat_val = f"{gs.test_statistic:.3f}" if gs.test_statistic is not None else "—"
            self.setItem(row, c, QTableWidgetItem(stat_val))
            self.item(row, c).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            c += 1

            # p-value
            p_val = f"{gs.p_value:.4f}" if gs.p_value is not None else "—"
            p_item = QTableWidgetItem(p_val)
            p_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if gs.p_value is not None and gs.p_value < 0.05:
                p_item.setBackground(QColor("#DCFCE7"))
            elif gs.p_value is not None:
                p_item.setBackground(QColor("#FEF9C3"))
            self.setItem(row, c, p_item)
            c += 1

            # Significance stars
            sig = _sig_label(gs.p_value)
            sig_item = QTableWidgetItem(sig)
            sig_item.setTextAlignment(Qt.AlignCenter)
            if sig and sig != "n.s.":
                sig_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                sig_item.setForeground(QColor("#15803D"))
            else:
                sig_item.setForeground(QColor("#9CA3AF"))
            self.setItem(row, c, sig_item)
            c += 1

            # Effect size
            eff_val = f"{gs.effect_size:.3f}" if gs.effect_size is not None else "—"
            self.setItem(row, c, QTableWidgetItem(eff_val))
            self.item(row, c).setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            c += 1

            # Effect type
            self.setItem(row, c, QTableWidgetItem(gs.effect_size_name or "—"))
            c += 1

        # Resize columns
        self.resizeColumnsToContents()
        cat_col_width = max(200, self.columnWidth(0))
        self.setColumnWidth(0, cat_col_width)


# ══════════════════════════════════════════════════════════════════════
# Compare Panel — orchestrator
# ══════════════════════════════════════════════════════════════════════

class ComparePanel(QWidget):
    """
    Group comparison panel.
    Top: configuration controls.
    Bottom: scrollable results table.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: Optional[QThread] = None
        self._group_names: List[str] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Config panel (top)
        self._config = _GroupConfigPanel()
        self._config.run_btn.clicked.connect(self._run_comparison)
        layout.addWidget(self._config)

        # Progress bar (hidden until running)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate
        self._progress.setFixedHeight(4)
        self._progress.setStyleSheet(
            "QProgressBar { border: none; background-color: #E5E7EB; }"
            "QProgressBar::chunk { background-color: #2563EB; }"
        )
        self._progress.hide()
        layout.addWidget(self._progress)

        # Status bar
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(32)
        self._status_bar.setStyleSheet("background-color: #EFF6FF; border-bottom: 1px solid #BFDBFE;")
        sb_layout = QHBoxLayout(self._status_bar)
        sb_layout.setContentsMargins(16, 0, 16, 0)
        self._status_lbl = QLabel(
            "Select a group column and click Run Comparison to see results."
        )
        self._status_lbl.setStyleSheet("color: #1D4ED8; font-size: 9pt;")
        sb_layout.addWidget(self._status_lbl)
        sb_layout.addStretch()

        export_btn = QPushButton("Export CSV…")
        export_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #1D4ED8; "
            "border: 1px solid #93C5FD; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #DBEAFE; }"
        )
        export_btn.clicked.connect(self._export_csv)
        sb_layout.addWidget(export_btn)

        layout.addWidget(self._status_bar)

        # Results table (main content)
        self._table = _ResultsTable()
        layout.addWidget(self._table, 1)

        # Empty state
        self._empty = QWidget()
        empty_layout = QVBoxLayout(self._empty)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_lbl = QLabel(
            "No comparison results yet.\n\n"
            "1. Run an analysis on the Analyze panel\n"
            "2. Select a group column above\n"
            "3. Click Run Comparison"
        )
        empty_lbl.setAlignment(Qt.AlignCenter)
        empty_lbl.setStyleSheet("color: #9CA3AF; font-size: 11pt;")
        empty_lbl.setWordWrap(True)
        empty_layout.addWidget(empty_lbl)
        layout.addWidget(self._empty)

        self._table.hide()

    # ------------------------------------------------------------------
    # Show event
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_columns()

    def _refresh_columns(self):
        from core.session import Session
        session = Session.instance()
        if session.raw_df is None:
            return

        # Suggest categorical columns for grouping
        from core.importer import detect_column_types
        infos = detect_column_types(session.raw_df)
        group_candidates = [
            i.name for i in infos
            if i.dtype in ("categorical", "text") and i.name != session.column_mapping.text_column
        ]
        if not group_candidates:
            group_candidates = [c for c in session.raw_df.columns
                                if c != session.column_mapping.text_column]

        self._config.populate_columns(group_candidates)

        # If session already has a group column, pre-select it
        gc = session.column_mapping.group_column
        if gc and gc in group_candidates:
            idx = self._config.group_col_combo.findText(gc)
            if idx >= 0:
                self._config.group_col_combo.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    # Run comparison
    # ------------------------------------------------------------------

    def _run_comparison(self):
        from core.session import Session
        from core.workers import StatisticsWorker

        session = Session.instance()

        if session.results.entry_scores is None:
            QMessageBox.information(self, "No Results", "Run an analysis first.")
            return

        group_col = self._config.selected_group_column
        if not group_col:
            QMessageBox.warning(self, "No Column", "Select a group column.")
            return

        if session.raw_df is None or group_col not in session.raw_df.columns:
            QMessageBox.warning(self, "Column Not Found",
                                f"Column '{group_col}' not found in the loaded data.")
            return

        # Align group series to scores length
        import pandas as pd
        group_series = session.raw_df[group_col].reset_index(drop=True)
        group_series = group_series.iloc[:len(session.results.entry_scores)]
        self._group_names = sorted(group_series.unique().tolist())

        if len(self._group_names) < 2:
            QMessageBox.warning(self, "Insufficient Groups",
                                f"Column '{group_col}' has only one unique value. "
                                "Need at least 2 groups to compare.")
            return

        self._progress.show()
        self._config.run_btn.setEnabled(False)
        self._status_lbl.setText(f"Running comparison across {len(self._group_names)} groups…")

        self._worker = StatisticsWorker(
            scores_df=session.results.entry_scores,
            group_series=group_series,
            nonparametric=self._config.nonparametric_cb.isChecked(),
            bonferroni=self._config.bonferroni_cb.isChecked(),
        )
        self._worker.finished.connect(self._on_comparison_done)
        self._worker.error.connect(self._on_comparison_error)
        self._worker.start()

        # Also store group column in session
        session.column_mapping.group_column = group_col

    def _on_comparison_done(self, group_stats: Dict):
        from core.session import Session
        session = Session.instance()
        session.results.group_stats = group_stats

        self._progress.hide()
        self._config.run_btn.setEnabled(True)

        n_sig = sum(
            1 for gs in group_stats.values()
            if gs.significant
        )
        self._status_lbl.setText(
            f"{len(group_stats)} categories compared · "
            f"{n_sig} significant (p < .05) · "
            f"Bonferroni correction {'applied' if self._config.bonferroni_cb.isChecked() else 'off'}"
        )

        self._table.load(group_stats, self._group_names)
        self._empty.hide()
        self._table.show()

    def _on_comparison_error(self, msg: str):
        self._progress.hide()
        self._config.run_btn.setEnabled(True)
        self._status_lbl.setText("Error running comparison.")
        QMessageBox.critical(self, "Comparison Error", msg)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_csv(self):
        from core.session import Session
        session = Session.instance()
        if not session.results.group_stats:
            QMessageBox.information(self, "No Data", "Run a comparison first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Comparison Results", "tass_group_comparison.csv", "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            rows = []
            for col_key, gs in session.results.group_stats.items():
                row: Dict[str, Any] = {
                    "category": col_key,
                    "test": gs.test_name,
                    "statistic": gs.test_statistic,
                    "p_value": gs.p_value,
                    "significant": gs.significant,
                    "effect_size": gs.effect_size,
                    "effect_size_type": gs.effect_size_name,
                }
                for g, desc in gs.group_descriptives.items():
                    for stat_name, val in desc.items():
                        row[f"{g}_{stat_name}"] = val
                rows.append(row)

            df = pd.DataFrame(rows)
            df.to_csv(path, index=False)
            from core.citation import citation_block
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(citation_block())
            QMessageBox.information(self, "Exported", f"Results saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))
