"""
TASS Main Window — shell with sidebar navigation and stacked content panels.
"""

from __future__ import annotations
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QSizePolicy,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QFrame,
)
from PySide6.QtCore import Qt, QSettings, QSize
from PySide6.QtGui import QAction, QFont, QKeySequence, QIcon


# Panel identifiers — order matches sidebar buttons
PANELS = [
    ("home",       "🏠", "Home"),
    ("import",     "📂", "Import"),
    ("analyze",    "🔬", "Analyze"),
    ("results",    "📊", "Results"),
    ("visualize",  "🎨", "Visualize"),
    ("compare",    "⚖️",  "Compare"),
    ("help",       "❓", "Help"),
]


class SidebarButton(QPushButton):
    """Icon + label nav button for the sidebar."""

    def __init__(self, icon_text: str, label: str, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFocusPolicy(Qt.NoFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setFixedHeight(56)
        self.setObjectName("sidebar_btn")

        # Stack icon over label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 6, 4, 4)
        layout.setSpacing(2)

        icon_lbl = QLabel(icon_text)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        icon_font = QFont()
        icon_font.setPointSize(14)
        icon_lbl.setFont(icon_font)

        text_lbl = QLabel(label)
        text_lbl.setAlignment(Qt.AlignCenter)
        text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        text_font = QFont()
        text_font.setPointSize(7)
        text_lbl.setFont(text_font)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)

    def setStyleSheet(self, style: str):
        # Allow stylesheet from parent to propagate; don't override
        super().setStyleSheet(style)


class MainWindow(QMainWindow):
    """
    Application shell.

    Sidebar provides navigation; central QStackedWidget holds one widget
    per panel. Panels are created lazily on first visit.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("TASS — Text Analysis for Social Scientists")
        self.setMinimumSize(1024, 700)
        self._set_window_icon()

        self._settings = QSettings("SIM DAD LLC", "TASS")
        self._restore_geometry()

        self._panel_widgets: dict[str, Optional[QWidget]] = {p[0]: None for p in PANELS}
        self._sidebar_buttons: dict[str, SidebarButton] = {}

        self._build_ui()
        self._build_menus()
        self._build_statusbar()

        # Start on home panel
        self.navigate_to("home")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(64)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(4, 8, 4, 8)
        sidebar_layout.setSpacing(4)

        # App abbreviation at top
        app_lbl = QLabel("T\nA\nS\nS")
        app_lbl.setObjectName("app_title_label")
        app_lbl.setAlignment(Qt.AlignCenter)
        title_font = QFont("Segoe UI", 9)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        app_lbl.setFont(title_font)
        app_lbl.setStyleSheet("color: #60A5FA; padding-bottom: 8px;")
        sidebar_layout.addWidget(app_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #2E3E52; margin: 0 4px;")
        sep.setFixedHeight(1)
        sidebar_layout.addWidget(sep)
        sidebar_layout.addSpacing(4)

        # Nav buttons
        for panel_id, icon, label in PANELS:
            btn = SidebarButton(icon, label)
            btn.setToolTip(label)
            btn.clicked.connect(lambda checked, pid=panel_id: self.navigate_to(pid))
            sidebar_layout.addWidget(btn)
            self._sidebar_buttons[panel_id] = btn

        sidebar_layout.addStretch()

        # Settings button at bottom
        settings_btn = SidebarButton("⚙️", "Settings")
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        sidebar_layout.addWidget(settings_btn)
        self._sidebar_buttons["settings"] = settings_btn

        root_layout.addWidget(sidebar)

        # Content area
        self._stack = QStackedWidget()
        self._stack.setObjectName("content_area")
        root_layout.addWidget(self._stack, 1)

        # Pre-load placeholder for every panel slot
        for panel_id, _, label in PANELS:
            placeholder = _PlaceholderPanel(label)
            self._panel_widgets[panel_id] = placeholder
            self._stack.addWidget(placeholder)

    def _build_menus(self):
        mb = self.menuBar()

        # File
        file_menu = mb.addMenu("&File")
        new_act = QAction("&New Analysis", self)
        new_act.setShortcut(QKeySequence.New)
        new_act.triggered.connect(self._new_analysis)
        file_menu.addAction(new_act)

        open_act = QAction("&Open Project…", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        save_act = QAction("&Save Project", self)
        save_act.setShortcut(QKeySequence.Save)
        save_act.triggered.connect(self._save_project)
        file_menu.addAction(save_act)

        save_as_act = QAction("Save Project &As…", self)
        save_as_act.setShortcut(QKeySequence.SaveAs)
        save_as_act.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_act)

        file_menu.addSeparator()

        import_act = QAction("&Import Data…", self)
        import_act.setShortcut("Ctrl+I")
        import_act.triggered.connect(lambda: self.navigate_to("import"))
        file_menu.addAction(import_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut(QKeySequence.Quit)
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Analysis
        analysis_menu = mb.addMenu("&Analysis")
        run_act = QAction("&Run Analysis…", self)
        run_act.setShortcut("Ctrl+R")
        run_act.triggered.connect(lambda: self.navigate_to("analyze"))
        analysis_menu.addAction(run_act)

        # Export
        export_menu = mb.addMenu("&Export")
        export_act = QAction("&Export Results…", self)
        export_act.setShortcut("Ctrl+E")
        export_act.triggered.connect(self._open_export)
        export_menu.addAction(export_act)

        cite_act = QAction("&How to Cite TASS…", self)
        cite_act.triggered.connect(self._open_cite)
        export_menu.addAction(cite_act)

        # Help
        help_menu = mb.addMenu("&Help")
        help_act = QAction("&Help", self)
        help_act.setShortcut(QKeySequence.HelpContents)
        help_act.triggered.connect(lambda: self.navigate_to("help"))
        help_menu.addAction(help_act)

        help_menu.addSeparator()

        license_act = QAction("&License / Activate…", self)
        license_act.triggered.connect(self._open_license)
        help_menu.addAction(license_act)

        about_act = QAction("&About TASS", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _build_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)

        self._license_label = QLabel("Not Activated")
        self._license_label.setStyleSheet("color: #888888; font-size: 9pt; padding-right: 8px;")
        sb.addPermanentWidget(self._license_label)

        self._status_label = QLabel("Ready")
        sb.addWidget(self._status_label)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to(self, panel_id: str):
        """Switch the central area to the named panel."""
        # Load real panel on first visit (lazy init)
        widget = self._get_or_load_panel(panel_id)
        self._stack.setCurrentWidget(widget)

        # Update sidebar button states
        for pid, btn in self._sidebar_buttons.items():
            btn.setChecked(pid == panel_id)
            # Inline style toggling for sidebar button active state
            if pid == panel_id:
                btn.setStyleSheet(
                    "background-color: #2563EB; color: #FFFFFF; border-radius: 6px;"
                )
            else:
                btn.setStyleSheet("")

        from core.session import Session
        Session.instance().ui_state["active_panel"] = panel_id

    def _get_or_load_panel(self, panel_id: str) -> QWidget:
        """Return existing widget or replace placeholder with real panel."""
        current = self._panel_widgets.get(panel_id)
        if current is not None and not isinstance(current, _PlaceholderPanel):
            return current

        real = self._create_panel(panel_id)
        if real is None:
            return current  # keep placeholder

        # Replace placeholder in stack
        if current is not None:
            idx = self._stack.indexOf(current)
            self._stack.removeWidget(current)
            current.deleteLater()
            self._stack.insertWidget(idx, real)
        else:
            self._stack.addWidget(real)

        self._panel_widgets[panel_id] = real
        return real

    def _create_panel(self, panel_id: str) -> Optional[QWidget]:
        """Instantiate the real panel widget for a given ID."""
        try:
            if panel_id == "home":
                from ui.welcome_screen import WelcomeScreen
                w = WelcomeScreen()
                w.new_analysis_requested.connect(lambda: self.navigate_to("import"))
                w.open_project_requested.connect(self._open_project)
                return w
            elif panel_id == "import":
                from ui.import_wizard import ImportWizard
                return ImportWizard()
            elif panel_id == "analyze":
                from ui.analysis_config_panel import AnalysisConfigPanel
                return AnalysisConfigPanel()
            elif panel_id == "results":
                from ui.results_panel import ResultsPanel
                return ResultsPanel()
            elif panel_id == "visualize":
                from ui.visualization_panel import VisualizationPanel
                return VisualizationPanel()
            elif panel_id == "compare":
                from ui.compare_panel import ComparePanel
                return ComparePanel()
            elif panel_id == "help":
                from ui.help_panel import HelpPanel
                return HelpPanel()
        except Exception as exc:
            # Panel not yet implemented — keep placeholder
            print(f"[TASS] Panel '{panel_id}' not loaded: {exc}")
        return None

    # ------------------------------------------------------------------
    # Public API used by app.py
    # ------------------------------------------------------------------

    def set_license_status(self, label: str):
        self._license_label.setText(label)
        # Color-code status
        if "Licensed" in label:
            self._license_label.setStyleSheet(
                "color: #16A34A; font-size: 9pt; font-weight: bold; padding-right: 8px;"
            )
        elif "Trial" in label and "Expired" not in label:
            self._license_label.setStyleSheet(
                "color: #D97706; font-size: 9pt; padding-right: 8px;"
            )
        elif "Expired" in label or "Not Activated" in label:
            self._license_label.setStyleSheet(
                "color: #DC2626; font-size: 9pt; padding-right: 8px;"
            )

    def set_status(self, message: str):
        self._status_label.setText(message)

    # ------------------------------------------------------------------
    # Menu action handlers
    # ------------------------------------------------------------------

    def _new_analysis(self):
        from core.session import Session
        if Session.instance().has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Start a new analysis anyway?",
                QMessageBox.Yes | QMessageBox.Cancel,
            )
            if reply != QMessageBox.Yes:
                return
        Session.reset()
        # Reload home panel fresh
        self._panel_widgets["home"] = None
        self.navigate_to("home")

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open TASS Project", "", "TASS Projects (*.tass)"
        )
        if not path:
            return
        try:
            from core.project import ProjectManager
            ProjectManager.load(path)
            self.set_status(f"Opened: {path}")
            self.navigate_to("results")
        except Exception as exc:
            QMessageBox.critical(self, "Error Opening Project", str(exc))

    def _save_project(self):
        from core.session import Session
        session = Session.instance()
        if not session.has_data:
            QMessageBox.information(self, "Nothing to Save", "Import data before saving a project.")
            return
        if session.project_path:
            self._do_save(session.project_path)
        else:
            self._save_project_as()

    def _save_project_as(self):
        from core.session import Session
        session = Session.instance()
        if not session.has_data:
            QMessageBox.information(self, "Nothing to Save", "Import data before saving a project.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save TASS Project", "", "TASS Projects (*.tass)"
        )
        if path:
            if not path.endswith(".tass"):
                path += ".tass"
            self._do_save(path)

    def _do_save(self, path: str):
        try:
            from core.project import ProjectManager
            ProjectManager.save(path)
            self.set_status(f"Saved: {path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error Saving Project", str(exc))

    def _open_export(self):
        from ui.export_dialog import ExportDialog
        dlg = ExportDialog(parent=self)
        dlg.exec()

    def _open_cite(self):
        from ui.cite_dialog import CiteDialog
        dlg = CiteDialog(parent=self)
        dlg.exec()

    def _open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dlg = SettingsDialog(parent=self)
        dlg.exec()

    def _open_license(self):
        from ui.license_dialog import LicenseDialog
        dlg = LicenseDialog(mode="activate", parent=self)
        if dlg.exec():
            from services.license import LicenseService
            status = LicenseService().get_status()
            self.set_license_status(status.display_label)

    def _show_about(self):
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sq_icon_path = os.path.join(base, "assets", "icons", "sq-icon.png")

        icon_html = ""
        if os.path.exists(sq_icon_path):
            # Use a file:// URL so QMessageBox can load the image
            uri = sq_icon_path.replace("\\", "/")
            icon_html = f'<p><img src="file:///{uri}" width="64" height="64"></p>'

        QMessageBox.about(
            self,
            "About TASS",
            f"{icon_html}"
            "<h3>TASS — Text Analysis for Social Scientists</h3>"
            "<p>Version 1.0.0</p>"
            "<p>© 2026 SIM DAD LLC. All rights reserved.</p>"
            "<p>A native Windows desktop tool for dictionary-based text analysis.</p>",
        )

    # ------------------------------------------------------------------
    # Window state persistence
    # ------------------------------------------------------------------

    def _set_window_icon(self):
        """Load app icon — SVG in dev, .ico when built with PyInstaller."""
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Prefer .ico (PyInstaller bundle); fall back to .svg (dev)
        for name in ("tass_icon.ico", "sq-icon.png", "app-icon.svg"):
            path = os.path.join(base, "assets", "icons", name)
            if os.path.exists(path):
                self.setWindowIcon(QIcon(path))
                break

    def _restore_geometry(self):
        geom = self._settings.value("mainwindow/geometry")
        if geom:
            self.restoreGeometry(geom)
        else:
            self.resize(1280, 800)

    def closeEvent(self, event):
        from core.session import Session
        if Session.instance().has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Quit without saving?",
                QMessageBox.Yes | QMessageBox.Cancel,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
        self._settings.setValue("mainwindow/geometry", self.saveGeometry())
        super().closeEvent(event)


# ------------------------------------------------------------------
# Placeholder panel (shown before real panel is loaded)
# ------------------------------------------------------------------

class _PlaceholderPanel(QWidget):
    """Minimal stand-in while a panel is not yet implemented."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        lbl = QLabel(label)
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        lbl.setFont(font)
        lbl.setStyleSheet("color: #CCCCCC;")
        lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl)

        sub = QLabel("Coming in next sprint")
        sub.setStyleSheet("color: #DDDDDD; font-size: 10pt;")
        sub.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub)
