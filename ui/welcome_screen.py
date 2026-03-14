"""
TASS Welcome / Home screen.
Shows recent projects, license status summary, and quick-start actions.
"""

from __future__ import annotations
import os
from typing import List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QFrame, QSizePolicy, QSpacerItem,
)
from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtGui import QFont


MAX_RECENT = 8


class WelcomeScreen(QWidget):
    """Home panel — recent projects list and quick-start buttons."""

    new_analysis_requested = Signal()
    open_project_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._settings = QSettings("SIM DAD LLC", "TASS")
        self._build_ui()
        self._load_recent_projects()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Left: hero / actions column
        left = QWidget()
        left.setFixedWidth(380)
        left.setStyleSheet("background-color: #1E2A38;")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(40, 60, 40, 40)
        left_layout.setSpacing(0)

        # Logo area
        logo_lbl = QLabel("TASS")
        logo_font = QFont("Segoe UI", 36)
        logo_font.setBold(True)
        logo_lbl.setFont(logo_font)
        logo_lbl.setStyleSheet("color: #60A5FA; letter-spacing: 6px;")
        left_layout.addWidget(logo_lbl)

        tagline = QLabel("Text Analysis\nfor Social Scientists")
        tagline.setStyleSheet("color: #94A3B8; font-size: 12pt; line-height: 1.4;")
        tagline.setWordWrap(True)
        left_layout.addWidget(tagline)
        left_layout.addSpacing(48)

        # Action buttons
        new_btn = QPushButton("+ New Analysis")
        new_btn.setFixedHeight(44)
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self.new_analysis_requested)
        left_layout.addWidget(new_btn)
        left_layout.addSpacing(12)

        open_btn = QPushButton("Open Project…")
        open_btn.setFixedHeight(44)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #60A5FA; "
            "border: 1px solid #60A5FA; border-radius: 6px; padding: 7px 16px; }"
            "QPushButton:hover { background-color: #1E3A5F; }"
        )
        open_btn.clicked.connect(self.open_project_requested)
        left_layout.addWidget(open_btn)
        left_layout.addStretch()

        # Version at bottom
        ver_lbl = QLabel("v1.0.0 · SIM DAD LLC")
        ver_lbl.setStyleSheet("color: #475569; font-size: 8pt;")
        left_layout.addWidget(ver_lbl)

        root.addWidget(left)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("background-color: #EEEEEE;")
        div.setFixedWidth(1)
        root.addWidget(div)

        # Right: recent projects
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(16)

        recent_heading = QLabel("Recent Projects")
        recent_font = QFont("Segoe UI", 14)
        recent_font.setBold(True)
        recent_heading.setFont(recent_font)
        recent_heading.setStyleSheet("color: #1A1A1A;")
        right_layout.addWidget(recent_heading)

        self._recent_list = QListWidget()
        self._recent_list.setAlternatingRowColors(True)
        self._recent_list.itemDoubleClicked.connect(self._open_recent)
        self._recent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        right_layout.addWidget(self._recent_list, 1)

        # Empty state label (shown when list is empty)
        self._empty_lbl = QLabel(
            "No recent projects.\n\nCreate a new analysis or open an existing .tass file."
        )
        self._empty_lbl.setAlignment(Qt.AlignCenter)
        self._empty_lbl.setStyleSheet("color: #AAAAAA; font-size: 10pt;")
        self._empty_lbl.setWordWrap(True)
        right_layout.addWidget(self._empty_lbl)

        # Tips section
        tips_frame = QFrame()
        tips_frame.setStyleSheet(
            "background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 8px;"
        )
        tips_layout = QVBoxLayout(tips_frame)
        tips_layout.setContentsMargins(16, 12, 16, 12)

        tips_heading = QLabel("Quick Start")
        tips_heading.setStyleSheet("color: #1D4ED8; font-weight: bold; font-size: 9pt;")
        tips_layout.addWidget(tips_heading)

        tips = QLabel(
            "1. Import a CSV, TXT, or Excel file\n"
            "2. Select dictionaries to apply\n"
            "3. Run the analysis\n"
            "4. Explore scores, charts, and group comparisons\n"
            "5. Export results for publication"
        )
        tips.setStyleSheet("color: #1E40AF; font-size: 9pt; line-height: 1.6;")
        tips_layout.addWidget(tips)

        right_layout.addWidget(tips_frame)

        root.addWidget(right, 1)

    # ------------------------------------------------------------------
    # Recent projects
    # ------------------------------------------------------------------

    def _load_recent_projects(self):
        paths: List[str] = self._settings.value("recent_projects", []) or []
        # Filter to existing files only
        paths = [p for p in paths if os.path.exists(p)]
        self._settings.setValue("recent_projects", paths)

        self._recent_list.clear()

        if not paths:
            self._recent_list.hide()
            self._empty_lbl.show()
            return

        self._empty_lbl.hide()
        self._recent_list.show()

        for path in paths[:MAX_RECENT]:
            name = os.path.splitext(os.path.basename(path))[0]
            item = QListWidgetItem(f"{name}\n{path}")
            item.setData(Qt.UserRole, path)
            item.setSizeHint(item.sizeHint().__class__(0, 52))
            self._recent_list.addItem(item)

    def _open_recent(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if not path:
            return
        try:
            from core.project import ProjectManager
            ProjectManager.load(path)
            # Signal main window to navigate to results
            parent = self.window()
            if hasattr(parent, "navigate_to"):
                parent.navigate_to("results")
        except Exception as exc:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error Opening Project", str(exc))

    @staticmethod
    def add_recent_project(path: str):
        """Call this whenever a project is saved/opened to update the recents list."""
        settings = QSettings("SIM DAD LLC", "TASS")
        paths: list = settings.value("recent_projects", []) or []
        if path in paths:
            paths.remove(path)
        paths.insert(0, path)
        settings.setValue("recent_projects", paths[:MAX_RECENT])
