"""
Import Wizard — Sprint 2.
Three-step flow: File Picker → Column Mapping → Data Preview.

Uses a QStackedWidget internally (not QWizard) for full visual control.
All file I/O happens synchronously here; threading added in Sprint 4 if needed.
"""

from __future__ import annotations
import os
from typing import List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFileDialog, QListWidget, QListWidgetItem,
    QComboBox, QScrollArea, QFrame, QCheckBox, QTableView,
    QAbstractItemView, QHeaderView, QMessageBox, QGroupBox,
)
from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QFont, QDragEnterEvent, QDropEvent

import pandas as pd


# ── Dtype badge colors ───────────────────────────────────────────────
DTYPE_COLORS = {
    "text":        ("#DBEAFE", "#1D4ED8"),
    "categorical": ("#DCFCE7", "#15803D"),
    "numeric":     ("#FEF3C7", "#B45309"),
    "datetime":    ("#F3E8FF", "#7E22CE"),
}


# ── Inline pandas → Qt model ─────────────────────────────────────────
class _PandasModel(QAbstractTableModel):
    _MAX_DISPLAY_ROWS = 2000

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df.iloc[: self._MAX_DISPLAY_ROWS]

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            return "" if pd.isna(val) else str(val)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            return str(section + 1)
        return None


# ══════════════════════════════════════════════════════════════════════
# Step header widget
# ══════════════════════════════════════════════════════════════════════

class _StepHeader(QWidget):
    """Shows step title, subtitle, and a 3-dot progress indicator."""

    def __init__(self, current: int, total: int, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        self.setFixedHeight(88)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(32, 0, 32, 0)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        step_lbl = QLabel(f"Step {current} of {total}")
        step_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        text_col.addWidget(step_lbl)

        title_lbl = QLabel(title)
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setStyleSheet("color: #111827;")
        text_col.addWidget(title_lbl)

        sub_lbl = QLabel(subtitle)
        sub_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        text_col.addWidget(sub_lbl)

        outer.addLayout(text_col)
        outer.addStretch()

        dot_row = QHBoxLayout()
        dot_row.setSpacing(8)
        for i in range(1, total + 1):
            dot = QLabel("●" if i == current else "○")
            dot.setStyleSheet(
                f"color: {'#2563EB' if i == current else '#D1D5DB'}; font-size: 14pt;"
            )
            dot_row.addWidget(dot)
        outer.addLayout(dot_row)


# ══════════════════════════════════════════════════════════════════════
# Step 1 — File Picker
# ══════════════════════════════════════════════════════════════════════

class _DropZone(QFrame):
    """Drag-and-drop target; click opens a file dialog."""

    files_dropped = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(160)
        self.setStyleSheet(
            "QFrame { border: 2px dashed #93C5FD; border-radius: 12px; "
            "background-color: #EFF6FF; }"
            "QFrame:hover { border-color: #2563EB; background-color: #DBEAFE; }"
        )

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        icon_lbl = QLabel("📂")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(28)
        icon_lbl.setFont(icon_font)
        layout.addWidget(icon_lbl)

        main_lbl = QLabel("Drop files here or click to browse")
        main_lbl.setAlignment(Qt.AlignCenter)
        main_lbl.setStyleSheet(
            "color: #2563EB; font-size: 11pt; font-weight: bold; border: none;"
        )
        layout.addWidget(main_lbl)

        hint_lbl = QLabel("CSV · TXT · XLSX · XLS")
        hint_lbl.setAlignment(Qt.AlignCenter)
        hint_lbl.setStyleSheet("color: #6B7280; font-size: 9pt; border: none;")
        layout.addWidget(hint_lbl)

    def mousePressEvent(self, event):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Data Files",
            "",
            "Data Files (*.csv *.txt *.xlsx *.xls);;All Files (*)",
        )
        if paths:
            self.files_dropped.emit(paths)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if paths:
            self.files_dropped.emit(paths)


class _Step1FileSelect(QWidget):
    next_requested = Signal(list)   # list[str] of file paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths: List[str] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(_StepHeader(
            1, 3, "Select Files",
            "Choose one or more data files to import"
        ))

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(40, 32, 40, 24)
        body_layout.setSpacing(16)

        self._drop_zone = _DropZone()
        self._drop_zone.files_dropped.connect(self._add_files)
        body_layout.addWidget(self._drop_zone)

        files_heading = QLabel("Selected files:")
        files_heading.setStyleSheet("font-weight: bold; color: #374151;")
        body_layout.addWidget(files_heading)

        self._file_list = QListWidget()
        self._file_list.setFixedHeight(120)
        self._file_list.setStyleSheet("font-size: 9pt;")
        body_layout.addWidget(self._file_list)

        clear_btn = QPushButton("Clear selection")
        clear_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #6B7280; "
            "border: 1px solid #D1D5DB; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        clear_btn.setFixedWidth(120)
        clear_btn.clicked.connect(self._clear_files)
        body_layout.addWidget(clear_btn, alignment=Qt.AlignLeft)

        body_layout.addStretch()

        nav = QHBoxLayout()
        nav.addStretch()
        self._next_btn = QPushButton("Next: Column Mapping →")
        self._next_btn.setFixedHeight(40)
        self._next_btn.setEnabled(False)
        self._next_btn.clicked.connect(lambda: self.next_requested.emit(self._paths))
        nav.addWidget(self._next_btn)
        body_layout.addLayout(nav)

        layout.addWidget(body, 1)

    def _add_files(self, paths: List[str]):
        for p in paths:
            if p not in self._paths:
                self._paths.append(p)
                item = QListWidgetItem(f"  {os.path.basename(p)}   —   {p}")
                item.setToolTip(p)
                self._file_list.addItem(item)
        self._next_btn.setEnabled(bool(self._paths))

    def _clear_files(self):
        self._paths.clear()
        self._file_list.clear()
        self._next_btn.setEnabled(False)


# ══════════════════════════════════════════════════════════════════════
# Step 2 — Column Mapping
# ══════════════════════════════════════════════════════════════════════

class _Step2ColumnMapping(QWidget):
    next_requested = Signal(str, object, list)  # text_col, group_col|None, meta_cols
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._meta_checks: List[QCheckBox] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(_StepHeader(
            2, 3, "Map Columns",
            "Tell TASS which column contains your text and optional grouping variable"
        ))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        body = QWidget()
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(40, 32, 40, 24)
        self._body_layout.setSpacing(24)
        scroll.setWidget(body)

        self._col_summary = QLabel()
        self._col_summary.setStyleSheet("color: #6B7280; font-size: 9pt;")
        self._body_layout.addWidget(self._col_summary)

        # Text column (required)
        text_group = QGroupBox("Text Column  (required)")
        text_group.setStyleSheet(
            "QGroupBox { border: 1.5px solid #2563EB; border-radius: 8px; "
            "margin-top: 10px; padding: 12px; }"
            "QGroupBox::title { color: #2563EB; font-weight: bold; "
            "subcontrol-origin: margin; subcontrol-position: top left; "
            "padding: 0 8px; background-color: #FFFFFF; }"
        )
        text_form = QVBoxLayout(text_group)
        text_desc = QLabel(
            "The column containing the text to be analyzed "
            "(e.g. survey responses, tweets, open-ended answers)."
        )
        text_desc.setWordWrap(True)
        text_desc.setStyleSheet("color: #6B7280; font-size: 9pt;")
        text_form.addWidget(text_desc)
        self._text_combo = QComboBox()
        self._text_combo.setFixedHeight(36)
        text_form.addWidget(self._text_combo)
        self._body_layout.addWidget(text_group)

        # Group column (optional)
        group_group = QGroupBox("Group Column  (optional)")
        group_group.setStyleSheet(
            "QGroupBox { border: 1px solid #D1D5DB; border-radius: 8px; "
            "margin-top: 10px; padding: 12px; }"
            "QGroupBox::title { color: #374151; font-weight: bold; "
            "subcontrol-origin: margin; subcontrol-position: top left; "
            "padding: 0 8px; background-color: #FFFFFF; }"
        )
        group_form = QVBoxLayout(group_group)
        group_desc = QLabel(
            "A column whose values define groups for comparison "
            "(e.g. political party, condition, country). Only categorical columns are shown."
        )
        group_desc.setWordWrap(True)
        group_desc.setStyleSheet("color: #6B7280; font-size: 9pt;")
        group_form.addWidget(group_desc)
        self._group_combo = QComboBox()
        self._group_combo.setFixedHeight(36)
        group_form.addWidget(self._group_combo)
        self._body_layout.addWidget(group_group)

        # Metadata columns (optional)
        meta_group = QGroupBox("Metadata Columns  (optional)")
        meta_group.setStyleSheet(
            "QGroupBox { border: 1px solid #D1D5DB; border-radius: 8px; "
            "margin-top: 10px; padding: 12px; }"
            "QGroupBox::title { color: #374151; font-weight: bold; "
            "subcontrol-origin: margin; subcontrol-position: top left; "
            "padding: 0 8px; background-color: #FFFFFF; }"
        )
        meta_form = QVBoxLayout(meta_group)
        meta_desc = QLabel(
            "Additional columns to carry through to exports (IDs, dates, URLs). "
            "They are not analyzed."
        )
        meta_desc.setWordWrap(True)
        meta_desc.setStyleSheet("color: #6B7280; font-size: 9pt;")
        meta_form.addWidget(meta_desc)

        self._meta_scroll = QScrollArea()
        self._meta_scroll.setWidgetResizable(True)
        self._meta_scroll.setFrameShape(QFrame.NoFrame)
        self._meta_scroll.setFixedHeight(120)
        self._meta_cb_widget = QWidget()
        self._meta_cb_layout = QVBoxLayout(self._meta_cb_widget)
        self._meta_cb_layout.setContentsMargins(0, 0, 0, 0)
        self._meta_cb_layout.setSpacing(4)
        self._meta_scroll.setWidget(self._meta_cb_widget)
        meta_form.addWidget(self._meta_scroll)
        self._body_layout.addWidget(meta_group)

        self._body_layout.addStretch()

        # Nav row
        nav = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #374151; "
            "border: 1px solid #D1D5DB; border-radius: 6px; padding: 7px 16px; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        back_btn.setFixedHeight(40)
        back_btn.clicked.connect(self.back_requested)
        nav.addWidget(back_btn)
        nav.addStretch()
        self._next_btn = QPushButton("Next: Preview Data →")
        self._next_btn.setFixedHeight(40)
        self._next_btn.clicked.connect(self._emit_next)
        nav.addWidget(self._next_btn)
        self._body_layout.addLayout(nav)

        layout.addWidget(scroll, 1)

    def load(self, df: pd.DataFrame, col_infos: list):
        self._col_summary.setText(
            f"{len(df):,} rows · {len(df.columns)} columns detected"
        )

        self._text_combo.clear()
        from core.importer import suggest_text_column
        suggested = suggest_text_column(df, col_infos)
        for info in col_infos:
            self._text_combo.addItem(f"{info.name}  [{info.dtype}]", userData=info.name)
        if suggested:
            idx = next((i for i, inf in enumerate(col_infos) if inf.name == suggested), 0)
            self._text_combo.setCurrentIndex(idx)

        self._group_combo.clear()
        self._group_combo.addItem("— None —", userData=None)
        for info in col_infos:
            if info.dtype in ("categorical", "text"):
                self._group_combo.addItem(f"{info.name}  [{info.dtype}]", userData=info.name)

        # Rebuild metadata checkboxes
        while self._meta_cb_layout.count():
            item = self._meta_cb_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._meta_checks = []
        for info in col_infos:
            cb = QCheckBox(f"{info.name}  [{info.dtype}]")
            cb.setProperty("col_name", info.name)
            self._meta_cb_layout.addWidget(cb)
            self._meta_checks.append(cb)

    def _emit_next(self):
        text_col = self._text_combo.currentData()
        if not text_col:
            QMessageBox.warning(self, "Selection Required", "Please select a text column.")
            return
        group_col = self._group_combo.currentData()
        meta_cols = [cb.property("col_name") for cb in self._meta_checks if cb.isChecked()]
        self.next_requested.emit(text_col, group_col, meta_cols)


# ══════════════════════════════════════════════════════════════════════
# Step 3 — Data Preview
# ══════════════════════════════════════════════════════════════════════

class _Step3Preview(QWidget):
    back_requested = Signal()
    analysis_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(_StepHeader(
            3, 3, "Preview & Confirm",
            "Verify the data looks correct, then proceed to analysis configuration"
        ))

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 16, 24, 16)
        body_layout.setSpacing(12)

        self._summary_lbl = QLabel()
        self._summary_lbl.setStyleSheet(
            "background-color: #EFF6FF; color: #1E40AF; "
            "border: 1px solid #BFDBFE; border-radius: 6px; padding: 8px 12px; font-size: 9pt;"
        )
        body_layout.addWidget(self._summary_lbl)

        self._mapping_lbl = QLabel()
        self._mapping_lbl.setStyleSheet("color: #374151; font-size: 9pt;")
        body_layout.addWidget(self._mapping_lbl)

        self._table = QTableView()
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setDefaultSectionSize(24)
        body_layout.addWidget(self._table, 1)

        self._truncation_lbl = QLabel()
        self._truncation_lbl.setStyleSheet("color: #9CA3AF; font-size: 8pt;")
        self._truncation_lbl.hide()
        body_layout.addWidget(self._truncation_lbl)

        nav = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #374151; "
            "border: 1px solid #D1D5DB; border-radius: 6px; padding: 7px 16px; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        back_btn.setFixedHeight(40)
        back_btn.clicked.connect(self.back_requested)
        nav.addWidget(back_btn)
        nav.addStretch()
        self._analyze_btn = QPushButton("✓  Confirm & Configure Analysis →")
        self._analyze_btn.setFixedHeight(40)
        self._analyze_btn.clicked.connect(self.analysis_requested)
        nav.addWidget(self._analyze_btn)
        body_layout.addLayout(nav)

        layout.addWidget(body, 1)

    def load(
        self,
        df: pd.DataFrame,
        text_col: str,
        group_col: Optional[str],
        meta_cols: List[str],
    ):
        n_rows, n_cols = df.shape
        self._summary_lbl.setText(
            f"{n_rows:,} rows · {n_cols} columns"
        )

        parts = [f"Text: <b>{text_col}</b>"]
        if group_col:
            parts.append(f"Group: <b>{group_col}</b>")
        if meta_cols:
            parts.append(f"Metadata: {', '.join(meta_cols)}")
        self._mapping_lbl.setText("  ·  ".join(parts))

        self._table.setModel(_PandasModel(df))

        if n_rows > _PandasModel._MAX_DISPLAY_ROWS:
            self._truncation_lbl.setText(
                f"Showing first {_PandasModel._MAX_DISPLAY_ROWS:,} of {n_rows:,} rows — "
                "all rows are included in the analysis."
            )
            self._truncation_lbl.show()
        else:
            self._truncation_lbl.hide()

        # Scroll text column to front
        if text_col in df.columns:
            text_idx = list(df.columns).index(text_col)
            self._table.horizontalHeader().moveSection(text_idx, 0)


# ══════════════════════════════════════════════════════════════════════
# ImportWizard — orchestrator
# ══════════════════════════════════════════════════════════════════════

class ImportWizard(QWidget):
    """
    Three-step import wizard.
    On completion, stores results in Session and signals parent to navigate
    to the analysis configuration panel.
    """

    import_complete = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._df: Optional[pd.DataFrame] = None
        self._text_col: Optional[str] = None
        self._group_col: Optional[str] = None
        self._meta_cols: List[str] = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack = QStackedWidget()
        layout.addWidget(self._stack)

        self._step1 = _Step1FileSelect()
        self._step2 = _Step2ColumnMapping()
        self._step3 = _Step3Preview()

        self._stack.addWidget(self._step1)
        self._stack.addWidget(self._step2)
        self._stack.addWidget(self._step3)

        self._step1.next_requested.connect(self._on_files_selected)
        self._step2.back_requested.connect(lambda: self._stack.setCurrentWidget(self._step1))
        self._step2.next_requested.connect(self._on_mapping_confirmed)
        self._step3.back_requested.connect(lambda: self._stack.setCurrentWidget(self._step2))
        self._step3.analysis_requested.connect(self._on_analysis_confirmed)

    # ------------------------------------------------------------------
    # Step transitions
    # ------------------------------------------------------------------

    def _on_files_selected(self, paths: List[str]):
        try:
            from core.importer import import_file, import_files, detect_column_types
            df = import_file(paths[0]) if len(paths) == 1 else import_files(paths)
        except Exception as exc:
            QMessageBox.critical(self, "Import Error", str(exc))
            return

        self._df = df
        col_infos = detect_column_types(df)
        self._step2.load(df, col_infos)
        self._stack.setCurrentWidget(self._step2)

    def _on_mapping_confirmed(self, text_col: str, group_col: Optional[str], meta_cols: List[str]):
        self._text_col = text_col
        self._group_col = group_col
        self._meta_cols = meta_cols
        self._step3.load(self._df, text_col, group_col, meta_cols)
        self._stack.setCurrentWidget(self._step3)

    def _on_analysis_confirmed(self):
        from core.session import Session
        session = Session.instance()
        session.raw_df = self._df
        session.column_mapping.text_column = self._text_col
        session.column_mapping.group_column = self._group_col
        session.column_mapping.metadata_columns = self._meta_cols
        if self._group_col:
            session.analysis_config.group_column = self._group_col

        parent_window = self.window()
        if hasattr(parent_window, "navigate_to"):
            parent_window.navigate_to("analyze")
            parent_window.set_status(
                f"Imported {len(self._df):,} rows · Text column: {self._text_col}"
            )

        self.import_complete.emit()
