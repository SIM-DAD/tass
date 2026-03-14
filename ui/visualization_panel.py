"""
Visualization Panel — Sprint 6.
Renders Matplotlib figures inside Qt using FigureCanvasQTAgg.
Supports: bar chart, word cloud, box plot, violin plot, heatmap.
Export to PNG (300 Dpi) and SVG.
"""

from __future__ import annotations
import os
from typing import Dict, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QFrame, QSizePolicy, QFileDialog,
    QMessageBox, QButtonGroup, QRadioButton, QGroupBox, QSplitter,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont

import matplotlib
matplotlib.use("Agg")

import matplotlib.figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg


# ══════════════════════════════════════════════════════════════════════
# Embedded figure canvas
# ══════════════════════════════════════════════════════════════════════

class _FigureCanvas(FigureCanvasQTAgg):
    """Thin wrapper so we can embed matplotlib figures in Qt layouts."""

    def __init__(self, fig: matplotlib.figure.Figure, parent=None):
        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self):
        return QSize(900, 500)


# ══════════════════════════════════════════════════════════════════════
# Chart type selector sidebar
# ══════════════════════════════════════════════════════════════════════

class _ChartTypeSidebar(QFrame):
    """Left panel: radio buttons for chart type + category/palette selectors."""

    CHART_TYPES = [
        ("bar",    "Bar Chart",   "Mean category scores"),
        ("cloud",  "Word Cloud",  "Matched word frequencies"),
        ("box",    "Box Plot",    "Score distributions by group"),
        ("violin", "Violin Plot", "Score distributions (richer)"),
        ("heat",   "Heatmap",     "Score matrix across categories"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("chart_sidebar")
        self.setFixedWidth(200)
        self.setFrameShape(QFrame.NoFrame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 8, 16)
        layout.setSpacing(12)

        hdr = QLabel("Chart Type")
        hdr.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(hdr)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        self._radios: Dict[str, QRadioButton] = {}

        for key, label, tooltip in self.CHART_TYPES:
            rb = QRadioButton(label)
            rb.setToolTip(tooltip)
            rb.setFont(QFont("Segoe UI", 9))
            self._btn_group.addButton(rb)
            self._radios[key] = rb
            layout.addWidget(rb)

        self._radios["bar"].setChecked(True)

        layout.addSpacing(8)
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E5E7EB;")
        layout.addWidget(sep)

        # Category selector (for box/violin single category)
        cat_hdr = QLabel("Category")
        cat_hdr.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(cat_hdr)

        self.category_combo = QComboBox()
        self.category_combo.setToolTip("Select which score category to chart")
        layout.addWidget(self.category_combo)

        layout.addSpacing(8)

        # Palette selector
        pal_hdr = QLabel("Color Palette")
        pal_hdr.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(pal_hdr)

        self.palette_combo = QComboBox()
        self.palette_combo.addItems(["default", "colorblind", "grayscale"])
        layout.addWidget(self.palette_combo)

        layout.addStretch()

    @property
    def selected_chart_type(self) -> str:
        for key, rb in self._radios.items():
            if rb.isChecked():
                return key
        return "bar"

    def populate_categories(self, categories: List[str]):
        self.category_combo.clear()
        for cat in categories:
            display = cat.split("__")[-1] if "__" in cat else cat
            self.category_combo.addItem(display, userData=cat)

    @property
    def selected_category(self) -> Optional[str]:
        return self.category_combo.currentData()

    @property
    def selected_palette(self) -> str:
        return self.palette_combo.currentText()


# ══════════════════════════════════════════════════════════════════════
# Visualization Panel
# ══════════════════════════════════════════════════════════════════════

class VisualizationPanel(QWidget):
    """
    Full chart display panel.
    Refreshes from Session when navigated to.
    Renders charts inline; supports PNG/SVG export.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_fig: Optional[matplotlib.figure.Figure] = None
        self._canvas: Optional[_FigureCanvas] = None
        self._build_ui()

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left sidebar
        self._sidebar = _ChartTypeSidebar()
        root.addWidget(self._sidebar)

        # Vertical separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #E5E7EB;")
        root.addWidget(sep)

        # Right: toolbar + canvas
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        root.addWidget(right, 1)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet("background-color: #F9FAFB; border-bottom: 1px solid #E5E7EB;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(8)

        self._title_label = QLabel("Visualization")
        self._title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        tb_layout.addWidget(self._title_label)
        tb_layout.addStretch()

        render_btn = QPushButton("Render Chart")
        render_btn.setStyleSheet(
            "QPushButton { background-color: #2563EB; color: white; "
            "border-radius: 6px; padding: 6px 16px; font-weight: bold; }"
            "QPushButton:hover { background-color: #1D4ED8; }"
        )
        render_btn.clicked.connect(self._render)
        tb_layout.addWidget(render_btn)

        export_png_btn = QPushButton("Export PNG")
        export_png_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #374151; "
            "border: 1px solid #D1D5DB; border-radius: 6px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        export_png_btn.clicked.connect(lambda: self._export("png"))
        tb_layout.addWidget(export_png_btn)

        export_svg_btn = QPushButton("Export SVG")
        export_svg_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #374151; "
            "border: 1px solid #D1D5DB; border-radius: 6px; padding: 6px 14px; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        export_svg_btn.clicked.connect(lambda: self._export("svg"))
        tb_layout.addWidget(export_svg_btn)

        right_layout.addWidget(toolbar)

        # Canvas area (scrollable)
        self._canvas_area = QScrollArea()
        self._canvas_area.setWidgetResizable(True)
        self._canvas_area.setStyleSheet("background-color: #FFFFFF;")
        right_layout.addWidget(self._canvas_area, 1)

        self._empty_widget = QWidget()
        empty_layout = QVBoxLayout(self._empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_lbl = QLabel(
            "No chart to display.\n\n"
            "Run an analysis first, then click Render Chart\n"
            "to generate a visualization."
        )
        empty_lbl.setAlignment(Qt.AlignCenter)
        empty_lbl.setStyleSheet("color: #9CA3AF; font-size: 11pt;")
        empty_lbl.setWordWrap(True)
        empty_layout.addWidget(empty_lbl)
        self._canvas_area.setWidget(self._empty_widget)

        # Connect sidebar controls
        self._sidebar._btn_group.buttonClicked.connect(self._on_chart_type_changed)
        self._sidebar.category_combo.currentIndexChanged.connect(
            lambda _: None  # auto-render on category change can be added later
        )

    # ------------------------------------------------------------------
    # Show event: refresh categories from session
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_categories()

    def _refresh_categories(self):
        from core.session import Session
        session = Session.instance()
        if session.results.entry_scores is not None:
            cols = list(session.results.entry_scores.columns)
            self._sidebar.populate_categories(cols)

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _on_chart_type_changed(self, btn):
        pass  # Could auto-render; for now user clicks Render

    def _render(self):
        from core.session import Session
        from core.visualization_engine import VisualizationEngine
        from core.statistics_engine import StatisticsEngine

        session = Session.instance()
        results = session.results

        if results.entry_scores is None:
            QMessageBox.information(self, "No Results", "Run an analysis before generating charts.")
            return

        self._refresh_categories()
        chart_type = self._sidebar.selected_chart_type
        palette = self._sidebar.selected_palette
        viz = VisualizationEngine(palette=palette)

        try:
            if chart_type == "bar":
                stats_eng = StatisticsEngine()
                summary = stats_eng.document_summary(results.entry_scores)
                fig = viz.bar_chart(summary, title="Mean Category Scores")
                title = "Bar Chart — Mean Scores"

            elif chart_type == "cloud":
                # Aggregate word_matches across all entries
                from collections import defaultdict
                agg: Dict[str, List[str]] = defaultdict(list)
                if results.word_matches:
                    for entry_matches in results.word_matches.values():
                        for cat, words in entry_matches.items():
                            agg[cat].extend(words)
                fig = viz.word_cloud(dict(agg), title="Word Cloud — Matched Words")
                title = "Word Cloud"

            elif chart_type in ("box", "violin"):
                cat = self._sidebar.selected_category
                if not cat:
                    QMessageBox.warning(self, "No Category", "Select a category from the sidebar.")
                    return

                group_col = session.column_mapping.group_column
                if group_col and session.raw_df is not None and group_col in session.raw_df.columns:
                    group_series = session.raw_df[group_col].reset_index(drop=True)
                    group_series = group_series.iloc[:len(results.entry_scores)]
                else:
                    # No groups — create a single dummy group
                    import pandas as pd
                    group_series = pd.Series(
                        ["All"] * len(results.entry_scores),
                        name="group"
                    )

                if chart_type == "box":
                    fig = viz.box_plot(results.entry_scores, group_series, cat)
                    title = f"Box Plot — {cat.split('__')[-1]}"
                else:
                    fig = viz.violin_plot(results.entry_scores, group_series, cat)
                    title = f"Violin Plot — {cat.split('__')[-1]}"

            elif chart_type == "heat":
                stats_eng = StatisticsEngine()
                summary = stats_eng.document_summary(results.entry_scores)
                fig = viz.heatmap(summary, title="Category Score Heatmap")
                title = "Heatmap"

            else:
                return

            self._display_figure(fig, title)

        except Exception as exc:
            QMessageBox.critical(self, "Chart Error", f"Failed to render chart:\n{exc}")

    def _display_figure(self, fig: matplotlib.figure.Figure, title: str):
        """Replace current canvas with new figure."""
        import matplotlib.pyplot as plt

        if self._canvas is not None:
            self._canvas.setParent(None)
            self._canvas.deleteLater()
            self._canvas = None

        if self._current_fig is not None:
            import matplotlib.pyplot as plt
            plt.close(self._current_fig)

        self._current_fig = fig
        self._canvas = _FigureCanvas(fig)
        self._canvas_area.setWidget(self._canvas)
        self._title_label.setText(title)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export(self, fmt: str):
        if self._current_fig is None:
            QMessageBox.information(self, "No Chart", "Render a chart before exporting.")
            return

        ext_filter = "PNG Image (*.png)" if fmt == "png" else "SVG Image (*.svg)"
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {fmt.upper()}", f"tass_chart.{fmt}", ext_filter
        )
        if not path:
            return

        try:
            from core.visualization_engine import VisualizationEngine
            VisualizationEngine().save_figure(self._current_fig, path)
            QMessageBox.information(self, "Exported", f"Chart saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))
