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
    QMessageBox, QAbstractItemView, QProgressBar, QFileDialog,
    QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QFont, QColor

import pandas as pd

from core.formatting import (
    format_p_apa, sig_stars, format_stat_with_df, effect_size_label,
    generate_apa_note,
)


def _sig_color(p: Optional[float]) -> Optional[QColor]:
    if p is None:
        return None
    if p < 0.05:
        return QColor("#D1FAE5")   # green tint
    return QColor("#FEF9C3")       # yellow tint


def _make_section_table(headers: List[str], rows: List[List], parent=None) -> QTableWidget:
    """Create a compact read-only table for a results section."""
    table = QTableWidget(len(rows), len(headers), parent)
    table.setHorizontalHeaderLabels(headers)
    table.setAlternatingRowColors(True)
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    table.horizontalHeader().setStretchLastSection(True)
    table.verticalHeader().setDefaultSectionSize(24)
    table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
    table.verticalHeader().setVisible(False)
    table.setFont(QFont("Segoe UI", 10))

    for r, row_data in enumerate(rows):
        for c, cell in enumerate(row_data):
            if isinstance(cell, tuple):
                text, color = cell
                item = QTableWidgetItem(str(text))
                if color:
                    item.setForeground(QColor(color))
            else:
                item = QTableWidgetItem(str(cell))
            item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            table.setItem(r, c, item)

    table.resizeColumnsToContents()
    # Size to content: header height + rows + small margin
    row_h = table.verticalHeader().defaultSectionSize()
    header_h = table.horizontalHeader().height()
    table.setFixedHeight(min(header_h + row_h * len(rows) + 4, 400))
    return table


def _collapsible_group(title: str, widget: QWidget) -> QGroupBox:
    """Wrap a widget in a checkable (collapsible) QGroupBox."""
    group = QGroupBox(title)
    group.setCheckable(True)
    group.setChecked(True)
    group.setFont(QFont("Segoe UI", 10, QFont.Bold))
    group.setStyleSheet(
        "QGroupBox { border: 1px solid #D1D5DB; border-radius: 6px; "
        "margin-top: 10px; padding: 6px; background-color: #FFFFFF; }"
        "QGroupBox::title { subcontrol-origin: margin; padding: 0 8px; "
        "color: #1F2937; background-color: #F9FAFB; }"
        "QGroupBox::indicator { width: 14px; height: 14px; }"
    )
    layout = QVBoxLayout(group)
    layout.setContentsMargins(4, 4, 4, 4)
    layout.addWidget(widget)
    group.toggled.connect(widget.setVisible)
    return group


# ══════════════════════════════════════════════════════════════════════
# Group Config Panel (top)
# ══════════════════════════════════════════════════════════════════════

class _GroupConfigPanel(QFrame):
    """Controls for selecting group factor, dependent variables, and test options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(
            "QFrame { background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 12)
        root.setSpacing(10)

        # ── Row 1: Factor (grouping variable) ──────────────────────────
        factor_row = QHBoxLayout()
        factor_row.setSpacing(10)

        lbl_factor = QLabel("Between-Subjects Factor:")
        lbl_factor.setFont(QFont("Segoe UI", 10, QFont.Bold))
        lbl_factor.setStyleSheet("border: none;")
        factor_row.addWidget(lbl_factor)

        self.group_col_combo = QComboBox()
        self.group_col_combo.setMinimumWidth(180)
        self.group_col_combo.setToolTip(
            "Select the column whose values define the groups to compare "
            "(e.g., gender, condition, party)."
        )
        factor_row.addWidget(self.group_col_combo)
        factor_row.addStretch()

        root.addLayout(factor_row)

        # ── Row 2: Dependent variables + options side by side ──────────
        body_row = QHBoxLayout()
        body_row.setSpacing(16)

        # Left: Dependent variable list
        dv_group = QGroupBox("Dependent Variable(s)")
        dv_group.setFont(QFont("Segoe UI", 10))
        dv_group.setStyleSheet(
            "QGroupBox { border: 1px solid #D1D5DB; border-radius: 6px; "
            "margin-top: 8px; padding: 4px; background-color: #FFFFFF; }"
            "QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; "
            "color: #374151; font-weight: bold; background-color: #F9FAFB; }"
        )
        dv_layout = QVBoxLayout(dv_group)
        dv_layout.setContentsMargins(8, 8, 8, 8)
        dv_layout.setSpacing(4)

        self._dv_hint = QLabel("Select the score columns to compare across groups.")
        self._dv_hint.setStyleSheet("color: #6B7280; font-size: 9pt; border: none;")
        self._dv_hint.setWordWrap(True)
        dv_layout.addWidget(self._dv_hint)

        self.dv_list = QListWidget()
        self.dv_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.dv_list.setStyleSheet(
            "QListWidget { border: 1px solid #E5E7EB; border-radius: 4px; "
            "background-color: #FFFFFF; }"
            "QListWidget::item { padding: 3px 4px; }"
        )
        self.dv_list.setMinimumHeight(80)
        self.dv_list.setMaximumHeight(160)
        dv_layout.addWidget(self.dv_list)

        # Select All / Deselect All
        sel_row = QHBoxLayout()
        sel_row.setSpacing(8)
        sel_all_btn = QPushButton("Select All")
        sel_all_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #2E7D5E; "
            "border: none; font-size: 9pt; padding: 2px 6px; }"
            "QPushButton:hover { text-decoration: underline; }"
        )
        sel_all_btn.clicked.connect(lambda: self._set_all_dvs(True))
        sel_row.addWidget(sel_all_btn)

        desel_btn = QPushButton("Deselect All")
        desel_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #6B7280; "
            "border: none; font-size: 9pt; padding: 2px 6px; }"
            "QPushButton:hover { text-decoration: underline; }"
        )
        desel_btn.clicked.connect(lambda: self._set_all_dvs(False))
        sel_row.addWidget(desel_btn)

        self._dv_count_lbl = QLabel("0 selected")
        self._dv_count_lbl.setStyleSheet("color: #9CA3AF; font-size: 9pt; border: none;")
        sel_row.addWidget(self._dv_count_lbl)
        sel_row.addStretch()
        dv_layout.addLayout(sel_row)

        body_row.addWidget(dv_group, stretch=2)

        # Right: Options + Run button
        opts_col = QVBoxLayout()
        opts_col.setSpacing(8)

        opts_group = QGroupBox("Options")
        opts_group.setFont(QFont("Segoe UI", 10))
        opts_group.setStyleSheet(
            "QGroupBox { border: 1px solid #D1D5DB; border-radius: 6px; "
            "margin-top: 8px; padding: 4px; background-color: #FFFFFF; }"
            "QGroupBox::title { subcontrol-origin: margin; padding: 0 6px; "
            "color: #374151; font-weight: bold; background-color: #F9FAFB; }"
        )
        opts_inner = QVBoxLayout(opts_group)
        opts_inner.setContentsMargins(8, 8, 8, 8)
        opts_inner.setSpacing(6)

        self.nonparametric_cb = QCheckBox("Non-parametric tests")
        self.nonparametric_cb.setFont(QFont("Segoe UI", 10))
        self.nonparametric_cb.setToolTip(
            "Mann-Whitney U (2 groups) or Kruskal-Wallis (3+ groups) "
            "instead of Welch t-test / ANOVA."
        )
        self.nonparametric_cb.setStyleSheet("border: none;")
        opts_inner.addWidget(self.nonparametric_cb)

        # Multiple comparison correction
        corr_row = QHBoxLayout()
        corr_row.setSpacing(6)
        corr_lbl = QLabel("Correction:")
        corr_lbl.setFont(QFont("Segoe UI", 10))
        corr_lbl.setStyleSheet("border: none;")
        corr_row.addWidget(corr_lbl)

        self.correction_combo = QComboBox()
        self.correction_combo.addItems(["Bonferroni", "FDR (Benjamini-Hochberg)", "None"])
        self.correction_combo.setToolTip(
            "Bonferroni: conservative, divides alpha by number of tests.\n"
            "FDR (Benjamini-Hochberg): controls false discovery rate; more powerful.\n"
            "None: no correction for multiple comparisons."
        )
        self.correction_combo.setStyleSheet("border: 1px solid #D1D5DB; border-radius: 4px;")
        corr_row.addWidget(self.correction_combo)
        opts_inner.addLayout(corr_row)

        opts_inner.addStretch()
        opts_col.addWidget(opts_group)

        self.run_btn = QPushButton("Run Comparison")
        self.run_btn.setStyleSheet(
            "QPushButton { background-color: #2E7D5E; color: white; "
            "border-radius: 6px; padding: 10px 24px; font-weight: bold; font-size: 11pt; }"
            "QPushButton:hover { background-color: #256B4E; }"
            "QPushButton:disabled { background-color: #9CA3AF; color: #E5E7EB; }"
        )
        self.run_btn.setEnabled(False)
        opts_col.addWidget(self.run_btn)

        body_row.addLayout(opts_col, stretch=1)
        root.addLayout(body_row)

    # ── Public API ─────────────────────────────────────────────────────

    def populate_columns(self, columns: List[str]):
        """Set available group (factor) columns."""
        self.group_col_combo.clear()
        for col in columns:
            self.group_col_combo.addItem(col)

    def populate_dependent_variables(self, score_columns: List[str]):
        """Set available dependent variable (score) columns. None checked by default."""
        self.dv_list.clear()
        for col in score_columns:
            # Show short name but store full key
            display = col.split("__")[-1] if "__" in col else col
            prefix = col.split("__")[0] + ": " if "__" in col else ""
            item = QListWidgetItem(f"{prefix}{display}")
            item.setData(Qt.UserRole, col)            # store full column key
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.dv_list.addItem(item)
        self._update_dv_count()
        self.dv_list.itemChanged.connect(self._update_dv_count)

    @property
    def selected_group_column(self) -> Optional[str]:
        return self.group_col_combo.currentText() or None

    @property
    def selected_dependent_variables(self) -> List[str]:
        """Return list of full column keys for checked DVs."""
        selected = []
        for i in range(self.dv_list.count()):
            item = self.dv_list.item(i)
            if item.checkState() == Qt.Checked:
                selected.append(item.data(Qt.UserRole))
        return selected

    # ── Private helpers ────────────────────────────────────────────────

    def _set_all_dvs(self, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        self.dv_list.blockSignals(True)
        for i in range(self.dv_list.count()):
            self.dv_list.item(i).setCheckState(state)
        self.dv_list.blockSignals(False)
        self._update_dv_count()

    def _update_dv_count(self):
        n = len(self.selected_dependent_variables)
        total = self.dv_list.count()
        self._dv_count_lbl.setText(f"{n} of {total} selected")
        self.run_btn.setEnabled(n > 0)


# ══════════════════════════════════════════════════════════════════════
# Structured Results Viewer
# ══════════════════════════════════════════════════════════════════════

class _StructuredResults(QScrollArea):
    """
    Structured output viewer with 5 collapsible sections:
    1. Descriptive Statistics
    2. Assumption Checks (Shapiro-Wilk + Levene's)
    3. Inferential Test Results
    4. Post-Hoc Comparisons
    5. Interpretive Notes (auto-generated APA sentences)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self._inner = QWidget()
        self._layout = QVBoxLayout(self._inner)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(8)
        self.setWidget(self._inner)

    def load(self, group_stats: Dict, group_names: List[str]):
        """Populate all sections from group comparison results."""
        # Clear previous content
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        sorted_stats = sorted(group_stats.items())

        self._build_descriptives(sorted_stats, group_names)
        self._build_assumptions(sorted_stats, group_names)
        self._build_inferential(sorted_stats, group_names)
        self._build_posthoc(sorted_stats)
        self._build_notes(sorted_stats)
        self._layout.addStretch()

    # ── Section 1: Descriptive Statistics ──────────────────────────────

    def _build_descriptives(self, sorted_stats, group_names):
        headers = ["Category"] + [f"{g}" for g in group_names]
        sub_headers = [""] + ["M (SD) [95% CI]"] * len(group_names)

        rows = []
        for col_key, gs in sorted_stats:
            cat = col_key.split("__")[-1] if "__" in col_key else col_key
            row = [cat]
            for g in group_names:
                desc = gs.group_descriptives.get(str(g), {})
                m, sd, n = desc.get("mean"), desc.get("std"), desc.get("n", 0)
                ci = gs.confidence_intervals.get(str(g))
                if m is not None and sd is not None:
                    cell = f"{m:.3f} ({sd:.3f}), N={n}"
                    if ci and ci[0] == ci[0]:  # not NaN
                        cell += f"  [{ci[0]:.3f}, {ci[1]:.3f}]"
                else:
                    cell = "—"
                row.append(cell)
            rows.append(row)

        table = _make_section_table(headers, rows)
        self._layout.addWidget(_collapsible_group("1. Descriptive Statistics", table))

    # ── Section 2: Assumption Checks ──────────────────────────────────

    def _build_assumptions(self, sorted_stats, group_names):
        headers = ["Category", "Shapiro-Wilk (Normality)", "Levene's (Equal Variance)"]
        rows = []
        for col_key, gs in sorted_stats:
            cat = col_key.split("__")[-1] if "__" in col_key else col_key

            # Normality summary
            non_normal = []
            for g in group_names:
                norm = gs.normality.get(str(g))
                if norm and not norm[2]:
                    non_normal.append(f"{g}: W = {norm[0]:.3f}, p = {format_p_apa(norm[1])}")
            if not gs.normality:
                norm_cell = "—"
            elif non_normal:
                norm_cell = ("Violated: " + "; ".join(non_normal), "#DC2626")
            else:
                norm_cell = ("All groups normal (p \u2265 .05)", "#16A34A")

            # Levene's
            if gs.levene:
                f_val, p_val, equal = gs.levene
                p_fmt = format_p_apa(p_val)
                if equal:
                    lev_cell = (f"F = {f_val:.2f}, p = {p_fmt} — equal variances assumed", "#16A34A")
                else:
                    lev_cell = (f"F = {f_val:.2f}, p = {p_fmt} — unequal variances", "#DC2626")
            else:
                lev_cell = "—"

            rows.append([cat, norm_cell, lev_cell])

        table = _make_section_table(headers, rows)
        self._layout.addWidget(_collapsible_group("2. Assumption Checks", table))

    # ── Section 3: Inferential Test Results ────────────────────────────

    def _build_inferential(self, sorted_stats, group_names):
        headers = ["Category", "Test", "Test Statistic", "p", "Sig.", "Effect Size", "Interpretation"]
        rows = []
        for col_key, gs in sorted_stats:
            cat = col_key.split("__")[-1] if "__" in col_key else col_key

            stat_apa = format_stat_with_df(gs.test_name, gs.test_statistic, gs.df_between, gs.df_within)
            p_apa = format_p_apa(gs.p_value)
            sig = sig_stars(gs.p_value)

            if sig and sig != "n.s.":
                sig_cell = (sig, "#15803D")
            else:
                sig_cell = ("n.s.", "#9CA3AF")

            if gs.p_value is not None and gs.p_value < 0.05:
                p_cell = (f"p = {p_apa}", "#15803D")
            else:
                p_cell = (f"p = {p_apa}", "#6B7280")

            if gs.effect_size is not None and gs.effect_size_name:
                eff_val = f"{gs.effect_size:.3f} ({gs.effect_size_name})"
            else:
                eff_val = "—"

            label = effect_size_label(gs.effect_size, gs.effect_size_name)
            if label == "large":
                label_cell = (label, "#DC2626")
            elif label == "medium":
                label_cell = (label, "#D97706")
            elif label == "small":
                label_cell = (label, "#2E7D5E")
            else:
                label_cell = (label or "—", "#9CA3AF")

            rows.append([cat, gs.test_name or "—", stat_apa, p_cell, sig_cell, eff_val, label_cell])

        table = _make_section_table(headers, rows)
        self._layout.addWidget(_collapsible_group("3. Inferential Test Results", table))

    # ── Section 4: Post-Hoc Comparisons ───────────────────────────────

    def _build_posthoc(self, sorted_stats):
        any_posthoc = any(gs.posthoc for _, gs in sorted_stats)
        if not any_posthoc:
            return

        # Collect method name
        methods = set()
        headers = ["Category", "Comparison", "p", "Sig."]
        rows = []
        for col_key, gs in sorted_stats:
            if not gs.posthoc:
                continue
            if gs.posthoc_method:
                methods.add(gs.posthoc_method)
            cat = col_key.split("__")[-1] if "__" in col_key else col_key
            for a, b, p, sig in gs.posthoc:
                p_fmt = format_p_apa(p)
                stars = sig_stars(p)
                sig_cell = (stars, "#15803D") if stars != "n.s." else ("n.s.", "#9CA3AF")
                rows.append([cat, f"{a} vs {b}", f"p = {p_fmt}", sig_cell])

        method_name = " / ".join(sorted(methods)) if methods else "Post-Hoc"
        table = _make_section_table(headers, rows)
        self._layout.addWidget(_collapsible_group(f"4. {method_name} Pairwise Comparisons", table))

    # ── Section 5: Interpretive Notes ─────────────────────────────────

    def _build_notes(self, sorted_stats):
        notes = []
        for _, gs in sorted_stats:
            note = generate_apa_note(gs)
            if note:
                notes.append(note)

        if not notes:
            return

        text_widget = QLabel("\n\n".join(notes))
        text_widget.setWordWrap(True)
        text_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_widget.setStyleSheet(
            "QLabel { color: #374151; font-size: 10pt; line-height: 1.6; "
            "padding: 12px; background-color: #F9FAFB; border: 1px solid #E5E7EB; "
            "border-radius: 6px; }"
        )

        self._layout.addWidget(_collapsible_group("5. Interpretive Notes (APA)", text_widget))


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
            "QProgressBar::chunk { background-color: #2E7D5E; }"
        )
        self._progress.hide()
        layout.addWidget(self._progress)

        # Status bar
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(32)
        self._status_bar.setStyleSheet("background-color: #ECFDF5; border-bottom: 1px solid #A7F3D0;")
        sb_layout = QHBoxLayout(self._status_bar)
        sb_layout.setContentsMargins(16, 0, 16, 0)
        self._status_lbl = QLabel(
            "Select a group column and click Run Comparison to see results."
        )
        self._status_lbl.setStyleSheet("color: #256B4E; font-size: 9pt;")
        sb_layout.addWidget(self._status_lbl)
        sb_layout.addStretch()

        export_btn = QPushButton("Export CSV…")
        export_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #256B4E; "
            "border: 1px solid #93C5FD; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #D1FAE5; }"
        )
        export_btn.clicked.connect(self._export_csv)
        sb_layout.addWidget(export_btn)

        layout.addWidget(self._status_bar)

        # Structured results viewer (main content)
        self._results = _StructuredResults()
        layout.addWidget(self._results, 1)

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

        self._results.hide()

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

        # Populate dependent variable list from score columns
        if session.results.entry_scores is not None:
            score_cols = session.results.entry_scores.columns.tolist()
            self._config.populate_dependent_variables(score_cols)

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
            QMessageBox.warning(self, "No Factor", "Select a between-subjects factor (group column).")
            return

        selected_dvs = self._config.selected_dependent_variables
        if not selected_dvs:
            QMessageBox.warning(self, "No Dependent Variables",
                                "Select at least one dependent variable (score column) to compare.")
            return

        if session.raw_df is None or group_col not in session.raw_df.columns:
            QMessageBox.warning(self, "Column Not Found",
                                f"Column '{group_col}' not found in the loaded data.")
            return

        # Filter scores to selected dependent variables only
        scores_filtered = session.results.entry_scores[selected_dvs]

        # Align group series to scores length
        import pandas as pd
        group_series = session.raw_df[group_col].reset_index(drop=True)
        group_series = group_series.iloc[:len(scores_filtered)]
        self._group_names = sorted(
            [str(v) for v in group_series.dropna().unique().tolist()]
        )

        if len(self._group_names) < 2:
            QMessageBox.warning(self, "Insufficient Groups",
                                f"Column '{group_col}' has only one unique value. "
                                "Need at least 2 groups to compare.")
            return

        self._progress.show()
        self._config.run_btn.setEnabled(False)
        n_dvs = len(selected_dvs)
        self._status_lbl.setText(
            f"Running comparison: {n_dvs} variable{'s' if n_dvs != 1 else ''} "
            f"across {len(self._group_names)} groups…"
        )

        # Map correction combo to engine parameter
        correction_map = {
            "Bonferroni": "bonferroni",
            "FDR (Benjamini-Hochberg)": "fdr",
            "None": "none",
        }
        correction = correction_map.get(
            self._config.correction_combo.currentText(), "bonferroni"
        )

        self._worker = StatisticsWorker(
            scores_df=scores_filtered,
            group_series=group_series,
            nonparametric=self._config.nonparametric_cb.isChecked(),
            correction=correction,
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
        corr_name = self._config.correction_combo.currentText()
        self._status_lbl.setText(
            f"{len(group_stats)} variable{'s' if len(group_stats) != 1 else ''} compared · "
            f"{n_sig} significant (p < .05) · "
            f"Correction: {corr_name}"
        )

        self._results.load(group_stats, self._group_names)
        self._empty.hide()
        self._results.show()

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
                    "df_between": gs.df_between,
                    "df_within": gs.df_within,
                    "p_value": gs.p_value,
                    "significant": gs.significant,
                    "effect_size": gs.effect_size,
                    "effect_size_type": gs.effect_size_name,
                    "effect_interpretation": effect_size_label(gs.effect_size, gs.effect_size_name),
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
