"""
Results Panel — Sprint 4.
Tabbed view populated from Session.results after analysis completes.

Tabs:
  0  Scores       — sortable entry-level scores table
  1  Word Matches — click an entry to see matched words highlighted
  2  Summary      — document-level aggregate statistics
  3  Groups       — CTA stub (wired fully in Sprint 5)
"""

from __future__ import annotations
from typing import Optional, Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTableView, QListWidget, QListWidgetItem,
    QTextBrowser, QSplitter, QFrame, QHeaderView,
    QAbstractItemView, QSizePolicy, QFileDialog, QMessageBox,
)
from PySide6.QtCore import (
    Qt, Signal, QAbstractTableModel, QModelIndex,
    QSortFilterProxyModel,
)
from PySide6.QtGui import QFont, QColor

import pandas as pd


# ── Category colour palette (cycles through these) ──────────────────
_CATEGORY_COLORS = [
    "#DBEAFE",  # blue
    "#DCFCE7",  # green
    "#FEF3C7",  # amber
    "#F3E8FF",  # purple
    "#FFEDD5",  # orange
    "#ECFEFF",  # cyan
    "#FCE7F3",  # pink
    "#F0FDF4",  # emerald
]


def _cat_color(index: int) -> str:
    return _CATEGORY_COLORS[index % len(_CATEGORY_COLORS)]


# ══════════════════════════════════════════════════════════════════════
# Pandas → Qt sortable table model
# ══════════════════════════════════════════════════════════════════════

class _SortableTableModel(QAbstractTableModel):
    """Wraps a DataFrame; supports sort via QSortFilterProxyModel."""

    _MAX_ROWS = 5000   # display cap (all rows still in session)

    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df.iloc[: self._MAX_ROWS].reset_index(drop=True)

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        val = self._df.iloc[index.row(), index.column()]
        if role == Qt.DisplayRole:
            if pd.isna(val):
                return ""
            if isinstance(val, float):
                return f"{val:.4f}"
            return str(val)
        if role == Qt.TextAlignmentRole:
            if isinstance(val, (int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # Shorten long column names: DictName__category → category\n(DictName)
                col = str(self._df.columns[section])
                if "__" in col:
                    d, c = col.split("__", 1)
                    return f"{c}\n({d})"
                return col
            return str(section + 1)
        return None


def _make_table_view(model: _SortableTableModel) -> QTableView:
    proxy = QSortFilterProxyModel()
    proxy.setSourceModel(model)

    view = QTableView()
    view.setModel(proxy)
    view.setSortingEnabled(True)
    view.setAlternatingRowColors(True)
    view.setSelectionMode(QAbstractItemView.SingleSelection)
    view.setSelectionBehavior(QAbstractItemView.SelectRows)
    view.setEditTriggers(QAbstractItemView.NoEditTriggers)
    view.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    view.horizontalHeader().setDefaultSectionSize(100)
    view.horizontalHeader().setStretchLastSection(False)
    view.verticalHeader().setDefaultSectionSize(22)
    view.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
    return view


# ══════════════════════════════════════════════════════════════════════
# Tab 0 — Scores
# ══════════════════════════════════════════════════════════════════════

class _ScoresTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header row
        hdr = QHBoxLayout()
        self._info_lbl = QLabel("No results yet.")
        self._info_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        hdr.addWidget(self._info_lbl)
        hdr.addStretch()

        export_btn = QPushButton("Export CSV…")
        export_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #2563EB; "
            "border: 1px solid #93C5FD; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #EFF6FF; }"
        )
        export_btn.clicked.connect(self._export_csv)
        hdr.addWidget(export_btn)

        layout.addLayout(hdr)

        self._view_container = QWidget()
        self._view_layout = QVBoxLayout(self._view_container)
        self._view_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view_container, 1)

        self._empty_lbl = QLabel(
            "Run an analysis to see entry-level scores here.\n\n"
            "Each row represents one text entry; columns are dictionary category scores."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #AAAAAA; font-size: 10pt;")
        self._empty_lbl.setWordWrap(True)
        self._view_layout.addWidget(self._empty_lbl)

        self._table: Optional[QTableView] = None
        self._df: Optional[pd.DataFrame] = None

    def load(self, scores_df: pd.DataFrame, text_col: Optional[str] = None):
        """Populate with entry-level scores, optionally prepending the text column."""
        from core.session import Session
        session = Session.instance()

        # Build display DataFrame: text col first, then scores
        display_df = scores_df.copy()
        if text_col and session.raw_df is not None and text_col in session.raw_df.columns:
            text_series = session.raw_df[text_col].reset_index(drop=True)
            display_df.insert(0, text_col, text_series.iloc[: len(display_df)].values)

        self._df = display_df
        n_rows, n_cats = len(scores_df), len(scores_df.columns)
        self._info_lbl.setText(
            f"{n_rows:,} entries · {n_cats} category scores · "
            f"Click a column header to sort"
        )

        # Remove previous table
        if self._table is not None:
            self._view_layout.removeWidget(self._table)
            self._table.deleteLater()
            self._table = None
        self._empty_lbl.hide()

        model = _SortableTableModel(display_df)
        self._table = _make_table_view(model)
        self._view_layout.addWidget(self._table)

        # Widen text column
        if text_col and text_col in display_df.columns:
            tc_idx = list(display_df.columns).index(text_col)
            self._table.horizontalHeader().resizeSection(tc_idx, 280)

    def _export_csv(self):
        if self._df is None:
            QMessageBox.information(self, "No Data", "Run an analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Scores", "", "CSV Files (*.csv)")
        if path:
            try:
                self._df.to_csv(path, index=False)
                QMessageBox.information(self, "Exported", f"Scores saved to:\n{path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error", str(exc))


# ══════════════════════════════════════════════════════════════════════
# Tab 1 — Word Matches
# ══════════════════════════════════════════════════════════════════════

class _WordMatchesTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._word_matches: Optional[Dict] = None
        self._texts: Optional[list] = None
        self._cat_color_map: Dict[str, str] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._empty_lbl = QLabel(
            "Run an analysis to explore word matches here.\n\n"
            "Click any entry in the left panel to see which words were matched "
            "and which dictionary categories they belong to."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #AAAAAA; font-size: 10pt; padding: 40px;")
        self._empty_lbl.setWordWrap(True)
        layout.addWidget(self._empty_lbl)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.hide()

        # Left: entry list
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 4, 8)
        left_layout.setSpacing(4)

        search_lbl = QLabel("Entries")
        search_font = QFont("Segoe UI", 9)
        search_font.setBold(True)
        search_lbl.setFont(search_font)
        left_layout.addWidget(search_lbl)

        self._entry_list = QListWidget()
        self._entry_list.setStyleSheet("font-size: 9pt;")
        self._entry_list.currentRowChanged.connect(self._on_entry_selected)
        left_layout.addWidget(self._entry_list, 1)

        self._splitter.addWidget(left)

        # Right: highlighted text + legend
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 8, 8, 8)
        right_layout.setSpacing(8)

        self._legend_widget = QWidget()
        self._legend_layout = QHBoxLayout(self._legend_widget)
        self._legend_layout.setContentsMargins(0, 0, 0, 0)
        self._legend_layout.setSpacing(12)
        right_layout.addWidget(self._legend_widget)

        self._text_browser = QTextBrowser()
        self._text_browser.setOpenLinks(False)
        self._text_browser.setStyleSheet("font-size: 10pt; line-height: 1.6;")
        right_layout.addWidget(self._text_browser, 1)

        self._splitter.addWidget(right)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 3)

        layout.addWidget(self._splitter)

    def load(self, word_matches: Dict, texts: list, categories: List[str]):
        self._word_matches = word_matches
        self._texts = texts

        # Assign a colour to each category
        self._cat_color_map = {cat: _cat_color(i) for i, cat in enumerate(categories)}

        self._empty_lbl.hide()
        self._splitter.show()

        self._entry_list.clear()
        for i, text in enumerate(texts):
            preview = str(text)[:80].replace("\n", " ")
            item = QListWidgetItem(f"{i + 1:>4}.  {preview}")
            item.setData(Qt.UserRole, i)
            self._entry_list.addItem(item)

        self._build_legend(categories)

        if self._entry_list.count() > 0:
            self._entry_list.setCurrentRow(0)

    def _build_legend(self, categories: List[str]):
        # Clear existing
        while self._legend_layout.count():
            item = self._legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for cat in categories[:8]:   # show up to 8 in legend
            short = cat.split("__")[-1] if "__" in cat else cat
            lbl = QLabel(short)
            bg = self._cat_color_map.get(cat, "#F3F4F6")
            lbl.setStyleSheet(
                f"background-color: {bg}; border-radius: 6px; "
                f"padding: 2px 8px; font-size: 8pt;"
            )
            self._legend_layout.addWidget(lbl)
        self._legend_layout.addStretch()

    def _on_entry_selected(self, row: int):
        if self._word_matches is None or self._texts is None or row < 0:
            return

        entry_idx = self._entry_list.item(row).data(Qt.UserRole)
        raw_text = str(self._texts[entry_idx])
        matches = self._word_matches.get(entry_idx, {})

        # Build a word → [categories] lookup for highlighting
        word_cats: Dict[str, List[str]] = {}
        for cat, words in matches.items():
            for w in words:
                word_cats.setdefault(w.lower(), []).append(cat)

        if not word_cats:
            self._text_browser.setPlainText(raw_text)
            return

        # Tokenize the display text preserving spacing, apply highlights
        html = self._build_html(raw_text, word_cats)
        self._text_browser.setHtml(html)

    def _build_html(self, text: str, word_cats: Dict[str, List[str]]) -> str:
        """
        Wrap matched words in coloured <mark> spans.
        Simple word-boundary approach (split on whitespace, re-join).
        """
        import re
        # Split preserving whitespace
        parts = re.split(r"(\s+)", text)
        html_parts = []
        for part in parts:
            clean = re.sub(r"[^\w]", "", part).lower()
            if clean in word_cats:
                cats = word_cats[clean]
                # Use first category's colour; tooltip shows all
                color = self._cat_color_map.get(cats[0], "#FEF3C7")
                labels = ", ".join(c.split("__")[-1] for c in cats)
                html_parts.append(
                    f'<mark style="background-color:{color}; border-radius:3px; '
                    f'padding:1px 2px;" title="{labels}">{part}</mark>'
                )
            else:
                html_parts.append(part.replace("<", "&lt;").replace(">", "&gt;"))

        return (
            '<html><body style="font-family: Segoe UI, sans-serif; '
            'font-size: 11pt; line-height: 1.7; padding: 8px;">'
            + "".join(html_parts)
            + "</body></html>"
        )


# ══════════════════════════════════════════════════════════════════════
# Tab 2 — Summary
# ══════════════════════════════════════════════════════════════════════

class _SummaryTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        hdr = QHBoxLayout()
        self._info_lbl = QLabel("Document-level aggregate statistics.")
        self._info_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        hdr.addWidget(self._info_lbl)
        hdr.addStretch()

        export_btn = QPushButton("Export CSV…")
        export_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #2563EB; "
            "border: 1px solid #93C5FD; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #EFF6FF; }"
        )
        export_btn.clicked.connect(self._export_csv)
        hdr.addWidget(export_btn)

        layout.addLayout(hdr)

        self._view_container = QWidget()
        vc_layout = QVBoxLayout(self._view_container)
        vc_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view_container, 1)

        self._empty_lbl = QLabel(
            "Run an analysis to see document-level statistics here.\n\n"
            "This tab shows mean, SD, min, max, and median for every dictionary category."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #AAAAAA; font-size: 10pt;")
        self._empty_lbl.setWordWrap(True)
        vc_layout.addWidget(self._empty_lbl)

        self._table: Optional[QTableView] = None
        self._vc_layout = vc_layout
        self._df: Optional[pd.DataFrame] = None

    def load(self, summary_df: pd.DataFrame):
        self._df = summary_df

        # Format numeric columns
        display = summary_df.copy()
        for col in display.columns:
            if col != "category" and pd.api.types.is_numeric_dtype(display[col]):
                display[col] = display[col].map(
                    lambda v: f"{v:.4f}" if pd.notna(v) else ""
                )

        self._info_lbl.setText(
            f"{len(summary_df)} categories · "
            "Stats: mean, SD, min, max, median, N"
        )

        if self._table is not None:
            self._vc_layout.removeWidget(self._table)
            self._table.deleteLater()
            self._table = None
        self._empty_lbl.hide()

        model = _SortableTableModel(display)
        self._table = _make_table_view(model)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._vc_layout.addWidget(self._table)

    def _export_csv(self):
        if self._df is None:
            QMessageBox.information(self, "No Data", "Run an analysis first.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Summary", "", "CSV Files (*.csv)")
        if path:
            try:
                self._df.to_csv(path, index=False)
                QMessageBox.information(self, "Exported", f"Summary saved to:\n{path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error", str(exc))


# ══════════════════════════════════════════════════════════════════════
# Tab 3 — Groups (CTA stub for Sprint 5)
# ══════════════════════════════════════════════════════════════════════

class _GroupsTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("⚖️")
        icon.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(32)
        icon.setFont(icon_font)
        layout.addWidget(icon)

        lbl = QLabel("Group Comparison")
        lbl.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 14)
        title_font.setBold(True)
        lbl.setFont(title_font)
        layout.addWidget(lbl)

        self._sub_lbl = QLabel(
            "Define groups and compare dictionary scores across them.\n"
            "t-tests, ANOVA, and effect sizes available.\n\n"
            "Set a group column in the Import step, then open the Compare panel."
        )
        self._sub_lbl.setAlignment(Qt.AlignCenter)
        self._sub_lbl.setStyleSheet("color: #6B7280; font-size: 10pt;")
        self._sub_lbl.setWordWrap(True)
        layout.addWidget(self._sub_lbl)

        compare_btn = QPushButton("Open Compare Panel →")
        compare_btn.setFixedWidth(200)
        compare_btn.clicked.connect(
            lambda: self.window().navigate_to("compare")
            if hasattr(self.window(), "navigate_to") else None
        )
        layout.addWidget(compare_btn, alignment=Qt.AlignCenter)

    def update_for_session(self):
        from core.session import Session
        session = Session.instance()
        gc = session.column_mapping.group_column
        if gc:
            self._sub_lbl.setText(
                f"Group column: <b>{gc}</b>\n\n"
                "Click the Compare panel to run group comparisons, view t-test / ANOVA results, "
                "and see per-group descriptive statistics."
            )


# ══════════════════════════════════════════════════════════════════════
# ResultsPanel — orchestrator
# ══════════════════════════════════════════════════════════════════════

class ResultsPanel(QWidget):
    """
    Four-tab results panel.
    Refreshes from Session automatically when navigated to.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top bar — shown only when results exist
        self._top_bar = QFrame()
        self._top_bar.setFixedHeight(40)
        self._top_bar.setStyleSheet(
            "background-color: #F0FDF4; border-bottom: 1px solid #BBF7D0;"
        )
        top_layout = QHBoxLayout(self._top_bar)
        top_layout.setContentsMargins(16, 0, 16, 0)

        self._top_info = QLabel()
        self._top_info.setStyleSheet("color: #15803D; font-size: 9pt; font-weight: bold;")
        top_layout.addWidget(self._top_info)
        top_layout.addStretch()

        rerun_btn = QPushButton("Re-configure Analysis →")
        rerun_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #15803D; "
            "border: 1px solid #86EFAC; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #DCFCE7; }"
        )
        rerun_btn.clicked.connect(
            lambda: self.window().navigate_to("analyze")
            if hasattr(self.window(), "navigate_to") else None
        )
        top_layout.addWidget(rerun_btn)
        self._top_bar.hide()

        layout.addWidget(self._top_bar)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        layout.addWidget(self._tabs, 1)

        self._scores_tab = _ScoresTab()
        self._matches_tab = _WordMatchesTab()
        self._summary_tab = _SummaryTab()
        self._groups_tab = _GroupsTab()

        self._tabs.addTab(self._scores_tab,   "📊  Scores")
        self._tabs.addTab(self._matches_tab,  "🔍  Word Matches")
        self._tabs.addTab(self._summary_tab,  "📋  Summary")
        self._tabs.addTab(self._groups_tab,   "⚖️  Groups")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_from_session()

    def load_results(
        self,
        entry_scores: pd.DataFrame,
        word_matches: Dict,
        summary: Optional[pd.DataFrame],
        group_stats=None,
    ):
        """Direct call (e.g. from analysis_config_panel after worker completes)."""
        self._populate(entry_scores, word_matches, summary)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _refresh_from_session(self):
        from core.session import Session
        session = Session.instance()
        results = session.results

        if results.entry_scores is None:
            return  # nothing to display yet

        self._populate(
            results.entry_scores,
            results.word_matches or {},
            results.document_summary,
        )

    def _populate(
        self,
        entry_scores: pd.DataFrame,
        word_matches: Dict,
        summary: Optional[pd.DataFrame],
    ):
        from core.session import Session
        session = Session.instance()

        n_rows = len(entry_scores)
        n_cats = len(entry_scores.columns)
        text_col = session.column_mapping.text_column

        self._top_info.setText(
            f"✓  Analysis complete · {n_rows:,} entries · {n_cats} category scores"
        )
        self._top_bar.show()

        # ── Scores tab ───────────────────────────────────────────────
        self._scores_tab.load(entry_scores, text_col)

        # ── Word Matches tab ─────────────────────────────────────────
        texts: list = []
        if session.raw_df is not None and text_col in session.raw_df.columns:
            texts = session.raw_df[text_col].fillna("").tolist()
        self._matches_tab.load(
            word_matches,
            texts,
            list(entry_scores.columns),
        )

        # ── Summary tab ──────────────────────────────────────────────
        if summary is not None:
            self._summary_tab.load(summary)

        # ── Groups tab ───────────────────────────────────────────────
        self._groups_tab.update_for_session()

        self._loaded = True
