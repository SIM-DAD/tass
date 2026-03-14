"""
Analysis Configuration Panel — Sprint 3.

Sections:
  1. Session status bar (data loaded / not loaded guard)
  2. Dictionary browser — cards with checkboxes, license badges, category previews
  3. Preprocessing options — lemmatization, stopwords, min token length
  4. Analysis levels — word / entry / document
  5. Group definition — shown only when a group column exists in session
  6. Run Analysis — launches AnalysisWorker + ProgressDialog
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QFrame, QFileDialog, QMessageBox,
    QGroupBox, QSpinBox, QSizePolicy, QButtonGroup, QListWidget,
    QListWidgetItem, QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


# ── License badge styling ────────────────────────────────────────────
_LICENSE_STYLES = {
    "MIT":                     ("#DCFCE7", "#15803D"),
    "CC-BY":                   ("#DBEAFE", "#1D4ED8"),
    "CC-BY-SA":                ("#F3E8FF", "#7E22CE"),
    "Apache 2.0":              ("#ECFEFF", "#0E7490"),
    "Princeton WordNet License": ("#FEF3C7", "#B45309"),
}
_DEFAULT_LICENSE_STYLE = ("#F3F4F6", "#6B7280")


def _license_badge(license_text: str) -> QLabel:
    lbl = QLabel(license_text)
    bg, fg = _LICENSE_STYLES.get(license_text, _DEFAULT_LICENSE_STYLE)
    lbl.setStyleSheet(
        f"background-color: {bg}; color: {fg}; border-radius: 8px; "
        f"padding: 2px 8px; font-size: 8pt; font-weight: bold;"
    )
    lbl.setFixedHeight(20)
    lbl.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    return lbl


# ══════════════════════════════════════════════════════════════════════
# Dictionary card widget
# ══════════════════════════════════════════════════════════════════════

class _DictCard(QFrame):
    """One card per available dictionary."""

    def __init__(self, entry: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._entry = entry
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1px solid #E5E7EB; "
            "border-radius: 8px; margin: 2px 4px; }"
            "QFrame:hover { border-color: #93C5FD; }"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(12)

        # Checkbox
        self._checkbox = QCheckBox()
        self._checkbox.setChecked(entry.get("enabled_by_default", False))
        self._checkbox.setFixedWidth(20)
        layout.addWidget(self._checkbox, alignment=Qt.AlignTop)

        # Text block
        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        # Name row
        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        name_lbl = QLabel(entry["display_name"])
        name_font = QFont("Segoe UI", 10)
        name_font.setBold(True)
        name_lbl.setFont(name_font)
        name_lbl.setStyleSheet("color: #111827;")
        name_row.addWidget(name_lbl)

        name_row.addWidget(_license_badge(entry.get("license", "unknown")))

        if entry.get("citation"):
            cite_lbl = QLabel(entry["citation"])
            cite_lbl.setStyleSheet("color: #9CA3AF; font-size: 8pt;")
            name_row.addWidget(cite_lbl)

        name_row.addStretch()
        text_col.addLayout(name_row)

        # Description
        desc_lbl = QLabel(entry.get("description", ""))
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        text_col.addWidget(desc_lbl)

        # Category preview tags
        cats = entry.get("categories_preview", [])
        if cats:
            cats_lbl = QLabel("Categories: " + " · ".join(cats[:6]))
            cats_lbl.setStyleSheet("color: #2563EB; font-size: 8pt;")
            cats_lbl.setWordWrap(True)
            text_col.addWidget(cats_lbl)

        layout.addLayout(text_col, 1)

        # Make clicking the card toggle the checkbox
        self.mousePressEvent = lambda e: self._checkbox.setChecked(not self._checkbox.isChecked())

    @property
    def dict_id(self) -> str:
        return self._entry["id"]

    @property
    def is_checked(self) -> bool:
        return self._checkbox.isChecked()

    def set_checked(self, checked: bool):
        self._checkbox.setChecked(checked)

    @property
    def checkbox(self) -> QCheckBox:
        return self._checkbox


# ══════════════════════════════════════════════════════════════════════
# Analysis Configuration Panel
# ══════════════════════════════════════════════════════════════════════

class AnalysisConfigPanel(QWidget):
    """
    Full analysis configuration panel.
    Wires dictionaries/registry → AnalysisWorker → ProgressDialog → Session.
    """

    analysis_complete = Signal()    # emitted when results stored in Session

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dict_cards: List[_DictCard] = []
        self._build_ui()
        self._populate_dictionaries()
        self._refresh_session_status()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Session status bar ───────────────────────────────────────
        self._status_bar = QFrame()
        self._status_bar.setFixedHeight(44)
        self._status_bar.setStyleSheet(
            "background-color: #EFF6FF; border-bottom: 1px solid #BFDBFE;"
        )
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)

        self._status_lbl = QLabel()
        self._status_lbl.setStyleSheet("color: #1E40AF; font-size: 9pt;")
        status_layout.addWidget(self._status_lbl)
        status_layout.addStretch()

        self._import_btn = QPushButton("← Import Data First")
        self._import_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #2563EB; "
            "border: 1px solid #93C5FD; border-radius: 4px; padding: 4px 12px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #DBEAFE; }"
        )
        self._import_btn.clicked.connect(
            lambda: self.window().navigate_to("import") if hasattr(self.window(), "navigate_to") else None
        )
        status_layout.addWidget(self._import_btn)

        root.addWidget(self._status_bar)

        # ── Main split: dict browser (left) | options (right) ───────
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background-color: #E5E7EB; }")

        # Left: Dictionary browser
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 8, 16)
        left_layout.setSpacing(10)

        # Browser header
        browser_hdr = QHBoxLayout()
        dict_title = QLabel("Dictionaries")
        title_font = QFont("Segoe UI", 12)
        title_font.setBold(True)
        dict_title.setFont(title_font)
        browser_hdr.addWidget(dict_title)
        browser_hdr.addStretch()

        select_all_btn = QPushButton("Select All")
        select_all_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #6B7280; "
            "border: 1px solid #D1D5DB; border-radius: 4px; padding: 3px 10px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        select_all_btn.clicked.connect(lambda: self._set_all_checked(True))
        browser_hdr.addWidget(select_all_btn)

        deselect_btn = QPushButton("Deselect All")
        deselect_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #6B7280; "
            "border: 1px solid #D1D5DB; border-radius: 4px; padding: 3px 10px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #F3F4F6; }"
        )
        deselect_btn.clicked.connect(lambda: self._set_all_checked(False))
        browser_hdr.addWidget(deselect_btn)

        left_layout.addLayout(browser_hdr)

        # Scroll area for cards
        self._dict_scroll = QScrollArea()
        self._dict_scroll.setWidgetResizable(True)
        self._dict_scroll.setFrameShape(QFrame.NoFrame)
        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.setSpacing(6)
        self._cards_layout.addStretch()
        self._dict_scroll.setWidget(self._cards_widget)
        left_layout.addWidget(self._dict_scroll, 1)

        # Import custom dictionary
        import_dict_btn = QPushButton("+ Import Custom Dictionary…")
        import_dict_btn.setStyleSheet(
            "QPushButton { background-color: transparent; color: #2563EB; "
            "border: 1px dashed #93C5FD; border-radius: 6px; padding: 8px; font-size: 9pt; }"
            "QPushButton:hover { background-color: #EFF6FF; }"
        )
        import_dict_btn.clicked.connect(self._import_custom_dictionary)
        left_layout.addWidget(import_dict_btn)

        splitter.addWidget(left)

        # Right: Options
        right = QWidget()
        right.setFixedWidth(300)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 16, 16, 16)
        right_layout.setSpacing(16)

        options_title = QLabel("Options")
        options_title_font = QFont("Segoe UI", 12)
        options_title_font.setBold(True)
        options_title.setFont(options_title_font)
        right_layout.addWidget(options_title)

        # Analysis levels
        levels_group = QGroupBox("Analysis Levels")
        levels_layout = QVBoxLayout(levels_group)
        levels_layout.setSpacing(6)

        self._level_word = QCheckBox("Word-level matches")
        self._level_word.setChecked(True)
        self._level_entry = QCheckBox("Entry-level scores")
        self._level_entry.setChecked(True)
        self._level_doc = QCheckBox("Document-level summary")
        self._level_doc.setChecked(True)
        for cb in (self._level_word, self._level_entry, self._level_doc):
            levels_layout.addWidget(cb)
        right_layout.addWidget(levels_group)

        # Preprocessing
        prep_group = QGroupBox("Preprocessing")
        prep_layout = QVBoxLayout(prep_group)
        prep_layout.setSpacing(6)

        self._opt_lemmatize = QCheckBox("Lemmatize tokens")
        self._opt_lemmatize.setToolTip(
            "Reduce words to base form (e.g. 'running' → 'run'). Slower but more accurate."
        )
        prep_layout.addWidget(self._opt_lemmatize)

        self._opt_stopwords = QCheckBox("Remove stopwords before matching")
        self._opt_stopwords.setToolTip(
            "Strip function words before matching. Only relevant for dictionaries "
            "that do not include stopwords."
        )
        prep_layout.addWidget(self._opt_stopwords)

        min_len_row = QHBoxLayout()
        min_len_row.addWidget(QLabel("Min token length:"))
        self._min_len_spin = QSpinBox()
        self._min_len_spin.setRange(1, 10)
        self._min_len_spin.setValue(1)
        self._min_len_spin.setFixedWidth(56)
        min_len_row.addWidget(self._min_len_spin)
        min_len_row.addStretch()
        prep_layout.addLayout(min_len_row)

        right_layout.addWidget(prep_group)

        # Group definition (shown only if session has a group column)
        self._group_group = QGroupBox("Group Definition")
        group_layout = QVBoxLayout(self._group_group)
        group_layout.setSpacing(6)

        self._group_info_lbl = QLabel()
        self._group_info_lbl.setStyleSheet("color: #6B7280; font-size: 9pt;")
        self._group_info_lbl.setWordWrap(True)
        group_layout.addWidget(self._group_info_lbl)

        self._group_values_list = QListWidget()
        self._group_values_list.setFixedHeight(100)
        self._group_values_list.setStyleSheet("font-size: 9pt;")
        group_layout.addWidget(self._group_values_list)

        right_layout.addWidget(self._group_group)
        self._group_group.hide()

        right_layout.addStretch()

        # Run analysis button
        self._run_btn = QPushButton("▶  Run Analysis")
        self._run_btn.setFixedHeight(48)
        self._run_btn.setStyleSheet(
            "QPushButton { background-color: #16A34A; color: #FFFFFF; "
            "border-radius: 8px; font-size: 12pt; font-weight: bold; }"
            "QPushButton:hover { background-color: #15803D; }"
            "QPushButton:disabled { background-color: #D1D5DB; color: #9CA3AF; }"
        )
        self._run_btn.clicked.connect(self._run_analysis)
        right_layout.addWidget(self._run_btn)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        root.addWidget(splitter, 1)

    # ------------------------------------------------------------------
    # Dictionary browser
    # ------------------------------------------------------------------

    def _populate_dictionaries(self):
        from dictionaries.registry import get_registry
        registry = get_registry()
        for entry in registry.all_entries():
            self._add_dict_card(entry)

    def _add_dict_card(self, entry: Dict[str, Any]):
        card = _DictCard(entry)
        # Insert before the trailing stretch
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
        self._dict_cards.append(card)

    def _set_all_checked(self, checked: bool):
        for card in self._dict_cards:
            card.set_checked(checked)

    def _import_custom_dictionary(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Custom Dictionary",
            "",
            "Dictionary Files (*.json);;All Files (*)",
        )
        if not path:
            return
        try:
            from dictionaries.registry import get_registry
            dict_id = get_registry().register_user_dictionary(path)
            entry = get_registry().get_entry(dict_id)
            self._add_dict_card(entry)
            QMessageBox.information(
                self, "Dictionary Imported",
                f"'{entry['display_name']}' has been added to the browser."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Import Error", str(exc))

    # ------------------------------------------------------------------
    # Session state refresh (called on panel show)
    # ------------------------------------------------------------------

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_session_status()

    def _refresh_session_status(self):
        from core.session import Session
        session = Session.instance()

        if session.has_data:
            self._status_lbl.setText(
                f"Data loaded: {session.row_count:,} rows · "
                f"Text column: {session.column_mapping.text_column}"
            )
            self._status_bar.setStyleSheet(
                "background-color: #F0FDF4; border-bottom: 1px solid #BBF7D0;"
            )
            self._status_lbl.setStyleSheet("color: #15803D; font-size: 9pt;")
            self._import_btn.hide()
            self._run_btn.setEnabled(True)

            # Show group definition if a group column exists
            gc = session.column_mapping.group_column
            if gc and session.raw_df is not None and gc in session.raw_df.columns:
                unique_vals = sorted(session.raw_df[gc].dropna().unique().tolist())
                self._group_info_lbl.setText(
                    f"Group column: {gc}\n{len(unique_vals)} unique values detected."
                )
                self._group_values_list.clear()
                for val in unique_vals:
                    item = QListWidgetItem(str(val))
                    item.setCheckState(Qt.Checked)
                    self._group_values_list.addItem(item)
                self._group_group.show()
            else:
                self._group_group.hide()
        else:
            self._status_lbl.setText("No data imported. Import a file before running analysis.")
            self._status_bar.setStyleSheet(
                "background-color: #FEF9C3; border-bottom: 1px solid #FDE68A;"
            )
            self._status_lbl.setStyleSheet("color: #92400E; font-size: 9pt;")
            self._import_btn.show()
            self._run_btn.setEnabled(False)
            self._group_group.hide()

    # ------------------------------------------------------------------
    # Run Analysis
    # ------------------------------------------------------------------

    def _run_analysis(self):
        from core.session import Session
        session = Session.instance()

        if not session.has_data:
            QMessageBox.warning(self, "No Data", "Import data before running analysis.")
            return

        selected_ids = [c.dict_id for c in self._dict_cards if c.is_checked]
        if not selected_ids:
            QMessageBox.warning(
                self, "No Dictionaries Selected",
                "Select at least one dictionary to analyze."
            )
            return

        # Trial row limit check
        from services.license import LicenseService
        if LicenseService().is_trial_row_limit_exceeded(session.row_count):
            QMessageBox.warning(
                self,
                "Trial Row Limit",
                f"Your trial allows up to 500 rows per analysis.\n"
                f"Your dataset has {session.row_count:,} rows.\n\n"
                "Upgrade to a full license to remove this limit.",
            )
            return

        # Write analysis config to session
        levels = []
        if self._level_word.isChecked():
            levels.append("word")
        if self._level_entry.isChecked():
            levels.append("entry")
        if self._level_doc.isChecked():
            levels.append("document")
        if not levels:
            levels = ["entry"]  # always have at least one level

        session.analysis_config.selected_dictionaries = selected_ids
        session.analysis_config.analysis_levels = levels

        # Group values filter
        gc = session.column_mapping.group_column
        if gc and self._group_group.isVisible():
            selected_groups = []
            for i in range(self._group_values_list.count()):
                item = self._group_values_list.item(i)
                if item.checkState() == Qt.Checked:
                    selected_groups.append(item.text())
            if selected_groups:
                session.analysis_config.groups = {gc: selected_groups}

        # Load dictionaries
        try:
            from dictionaries.registry import get_registry
            dictionaries = get_registry().load_multiple(selected_ids)
        except Exception as exc:
            QMessageBox.critical(self, "Dictionary Load Error", str(exc))
            return

        # Build preprocessor config
        from core.preprocessor import Preprocessor
        preprocessor_kwargs = {
            "lowercase": True,
            "strip_punctuation": True,
            "remove_stopwords": self._opt_stopwords.isChecked(),
            "lemmatize": self._opt_lemmatize.isChecked(),
            "min_token_length": self._min_len_spin.value(),
        }

        # Launch worker + progress dialog
        self._launch_worker(session, dictionaries, preprocessor_kwargs)

    def _launch_worker(self, session, dictionaries: list, preprocessor_kwargs: dict):
        from core.workers import AnalysisWorker
        from ui.progress_dialog import ProgressDialog

        # Store for access in callbacks
        self._worker = AnalysisWorker(
            raw_df=session.raw_df,
            text_column=session.column_mapping.text_column,
            dictionaries=dictionaries,
            analysis_config=session.analysis_config,
        )

        self._progress = ProgressDialog("Running Analysis…", parent=self)
        self._progress.set_indeterminate("Initializing…")

        # Connect signals
        self._worker.progress.connect(self._progress.update_progress)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._progress.cancel_requested.connect(self._worker.cancel)

        self._worker.start()
        self._progress.exec()  # blocks until finish() or reject()

    def _on_analysis_finished(self, entry_scores, word_matches):
        from core.session import Session
        from core.statistics_engine import StatisticsEngine
        session = Session.instance()

        session.results.entry_scores = entry_scores
        session.results.word_matches = word_matches

        # Document-level summary (fast, run synchronously)
        try:
            engine = StatisticsEngine()
            summary = engine.document_summary(entry_scores)
            session.results.document_summary = summary
        except Exception:
            pass

        self._progress.finish()

        parent_window = self.window()
        if hasattr(parent_window, "navigate_to"):
            n_cats = len(entry_scores.columns) if entry_scores is not None else 0
            parent_window.set_status(
                f"Analysis complete · {session.row_count:,} entries · {n_cats} category scores"
            )
            parent_window.navigate_to("results")

        self.analysis_complete.emit()

    def _on_analysis_error(self, error_msg: str):
        self._progress.reject()
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"The analysis failed with the following error:\n\n{error_msg}",
        )
