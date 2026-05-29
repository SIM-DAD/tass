"""
Crash-reporting dialogs — the three touchpoints from the SIM DAD LLC
Error-Reporting Policy (section 3):

  A. FirstLaunchPrefDialog  — first-launch opt-in preference
  B. LiveCrashDialog        — shown when an unhandled exception is caught
  C. PostRestartDialog      — surfaces queued reports on the next launch

Plus QueuedReportsDialog, the "View queued reports" manager opened from
Settings -> Privacy.

Every path is manual-submit: nothing is sent without the user clicking
"Send via email", which opens their own mail client via a mailto: URL. There
is no SMTP, no background uploader, no telemetry.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QRadioButton,
    QButtonGroup, QPlainTextEdit, QCheckBox, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QApplication,
)
from PySide6.QtGui import QFont, QDesktopServices
from PySide6.QtCore import Qt, QUrl

from services import error_reporter as er
from services.settings_manager import SettingsManager


# Canonical disclosure shown by every "What's in a crash report?" link
# (policy section 4.4).
EXAMPLE_REPORT = """\
Product: TASS
Version: 1.0.0
Crash time: 2026-05-23 18:42:10 UTC

OS: Windows 11.0.26200
CPU: Intel Core i7-11700K
RAM: 64 GB
Python: 3.12.4

Traceback (most recent call last):
  File "<redacted-path>/dictionary_engine.py", line 152, in analyze
    score = self._compute_idf(...)
  File "<redacted-path>/dictionary_engine.py", line 218, in _compute_idf
    return math.log(n_docs / (1 + df_counts[t]))
ZeroDivisionError: float division by zero"""

# Live-crash dialog outcomes.
ACTION_SEND = "send"
ACTION_COPY = "copy"
ACTION_SAVE = "save"
ACTION_DISMISS = "dismiss"   # user clicked "Don't send"
ACTION_CLOSED = "closed"     # user closed the window without choosing

_MONO = QFont("Consolas", 9)
_MONO.setStyleHint(QFont.Monospace)


def _settings() -> SettingsManager:
    return SettingsManager.instance()


def _report_view(text: str) -> QPlainTextEdit:
    view = QPlainTextEdit()
    view.setPlainText(text)
    view.setReadOnly(True)
    view.setFont(_MONO)
    view.setMinimumHeight(220)
    return view


def show_whats_in_a_report(parent=None) -> None:
    """Display the canonical example report (the section 4 disclosure)."""
    dlg = QDialog(parent)
    dlg.setWindowTitle("What's in a crash report?")
    dlg.setModal(True)
    dlg.setMinimumWidth(560)
    layout = QVBoxLayout(dlg)
    layout.setContentsMargins(20, 20, 20, 16)
    intro = QLabel(
        "A crash report contains only the technical error plus your TASS "
        "version, operating system, and hardware specs. File paths are "
        "redacted. No documents, dictionary contents, or analysis data are "
        "ever included. A report looks like this:"
    )
    intro.setWordWrap(True)
    layout.addWidget(intro)
    layout.addWidget(_report_view(EXAMPLE_REPORT))
    btn_row = QHBoxLayout()
    btn_row.addStretch()
    close_btn = QPushButton("Close")
    close_btn.clicked.connect(dlg.accept)
    btn_row.addWidget(close_btn)
    layout.addLayout(btn_row)
    dlg.exec()


# ----------------------------------------------------------------------
# Touchpoint A — first-launch preference
# ----------------------------------------------------------------------


class FirstLaunchPrefDialog(QDialog):
    """Asks once whether the user wants crash prompts. Writes the preference."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help improve TASS")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        body = QLabel(
            "If TASS crashes, would you like to be prompted to send a crash "
            "report? Reports contain only the technical error, your TASS "
            "version, your operating system, and your hardware specs. No "
            "documents, dictionary contents, or analysis data are ever "
            "included. You will see the full report contents before anything "
            "is sent. You can change this anytime in Settings → Privacy."
        )
        body.setWordWrap(True)
        layout.addWidget(body)

        self._group = QButtonGroup(self)
        self._opt_prompt = QRadioButton("Prompt me when TASS crashes")
        self._opt_never = QRadioButton("Never prompt me — handle crash reports manually")
        self._opt_prompt.setChecked(True)
        self._group.addButton(self._opt_prompt)
        self._group.addButton(self._opt_never)
        layout.addWidget(self._opt_prompt)
        layout.addWidget(self._opt_never)

        link = QPushButton("What's in a crash report?")
        link.setFlat(True)
        link.setCursor(Qt.PointingHandCursor)
        link.setStyleSheet("QPushButton { color: #2E7D5E; border: none; text-align: left; }")
        link.clicked.connect(lambda: show_whats_in_a_report(self))
        layout.addWidget(link)

        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cont = QPushButton("Continue")
        cont.setDefault(True)
        cont.clicked.connect(self._on_continue)
        btn_row.addWidget(cont)
        layout.addLayout(btn_row)

    def _on_continue(self):
        _settings().set(er.KEY_PROMPT_ON_CRASH, self._opt_prompt.isChecked())
        _settings().set(er.KEY_FIRST_LAUNCH_PROMPT_SHOWN, True)
        self.accept()

    @staticmethod
    def maybe_show(parent=None) -> None:
        """Show the preference dialog only once, on the very first launch."""
        if _settings().get(er.KEY_FIRST_LAUNCH_PROMPT_SHOWN, False):
            return
        FirstLaunchPrefDialog(parent).exec()


# ----------------------------------------------------------------------
# Touchpoint B — live crash dialog
# ----------------------------------------------------------------------


class LiveCrashDialog(QDialog):
    """Shown by the top-level exception handler. Manual submit only.

    After the dialog closes, inspect ``.action`` (ACTION_*) and
    ``.dont_show_again``. If ``.action == ACTION_CLOSED`` the caller should
    queue the report for review on next launch.
    """

    def __init__(self, report: er.CrashReport, opted_in: bool, parent=None):
        super().__init__(parent)
        self._report = report
        self._report_text = er.format_report_text(report)
        self.action: str | None = None
        self.dont_show_again = False

        self.setWindowTitle("TASS encountered an error")
        self.setModal(True)
        self.setMinimumWidth(600)
        self._build_ui(opted_in)

    def _build_ui(self, opted_in: bool):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(12)

        body = QLabel(
            "An error occurred and TASS may need to close. You can help by "
            "sending us this report. The full contents are shown below — "
            "nothing else will be sent."
        )
        body.setWordWrap(True)
        layout.addWidget(body)

        # Report contents. Expanded by default when the user opted in.
        self._toggle = QPushButton()
        self._toggle.setFlat(True)
        self._toggle.setCursor(Qt.PointingHandCursor)
        self._toggle.setStyleSheet("QPushButton { color: #2E7D5E; border: none; text-align: left; }")
        self._toggle.clicked.connect(self._toggle_details)
        layout.addWidget(self._toggle)

        self._view = _report_view(self._report_text)
        layout.addWidget(self._view)
        self._set_details_visible(opted_in)

        self._dont_show = QCheckBox("Don't show this dialog again")
        layout.addWidget(self._dont_show)

        # Action buttons.
        btn_row = QHBoxLayout()
        what = QPushButton("What gets sent?")
        what.setFlat(True)
        what.setCursor(Qt.PointingHandCursor)
        what.setStyleSheet("QPushButton { color: #2E7D5E; border: none; }")
        what.clicked.connect(lambda: show_whats_in_a_report(self))
        btn_row.addWidget(what)
        btn_row.addStretch()

        dont = QPushButton("Don't send")
        dont.clicked.connect(self._on_dismiss)
        btn_row.addWidget(dont)

        save = QPushButton("Save report to file…")
        save.clicked.connect(self._on_save)
        btn_row.addWidget(save)

        copy = QPushButton("Copy report to clipboard")
        copy.clicked.connect(self._on_copy)
        btn_row.addWidget(copy)

        send = QPushButton("Send via email")
        send.clicked.connect(self._on_send)
        btn_row.addWidget(send)

        layout.addLayout(btn_row)

        # Focus the policy-appropriate default.
        (send if opted_in else dont).setDefault(True)

    def _set_details_visible(self, visible: bool):
        self._view.setVisible(visible)
        self._toggle.setText("Hide report details" if visible else "Show report details")

    def _toggle_details(self):
        self._set_details_visible(not self._view.isVisible())

    # -- actions --------------------------------------------------------

    def _capture_checkbox(self):
        if self._dont_show.isChecked():
            self.dont_show_again = True
            _settings().set(er.KEY_PROMPT_ON_CRASH, False)

    def _on_send(self):
        self.action = ACTION_SEND
        self._capture_checkbox()
        QDesktopServices.openUrl(QUrl(er.compose_mailto(self._report)))
        self.accept()

    def _on_copy(self):
        self.action = ACTION_COPY
        QApplication.clipboard().setText(self._report_text)
        QMessageBox.information(
            self, "Copied",
            "The crash report was copied to your clipboard. You can paste it "
            f"into an email to {er.SUPPORT_INBOX}.",
        )

    def _on_save(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save crash report",
            f"tass-crash-{self._report.crash_timestamp.replace(':', '').replace('-', '')}.txt",
            "Text files (*.txt)",
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self._report_text)
            self.action = ACTION_SAVE
            QMessageBox.information(self, "Saved", "The crash report was saved.")
        except Exception as exc:
            QMessageBox.warning(self, "Could not save", str(exc))

    def _on_dismiss(self):
        self.action = ACTION_DISMISS
        self._capture_checkbox()
        self.reject()

    def closeEvent(self, event):
        if self.action is None:
            self.action = ACTION_CLOSED
        super().closeEvent(event)


# ----------------------------------------------------------------------
# Touchpoint C — post-crash relaunch
# ----------------------------------------------------------------------


def _review_one(path, parent=None) -> None:
    """Open a queued report in the live-crash review UI; delete it if sent."""
    report = er.load_queued(path)
    if report is None:
        er.delete_queued(path)  # unreadable file — drop it
        return
    dlg = LiveCrashDialog(report, opted_in=True, parent=parent)
    dlg.exec()
    if dlg.action == ACTION_SEND:
        er.delete_queued(path)


class PostRestartDialog(QDialog):
    """Surfaces queued reports from a prior session. Never auto-sends."""

    def __init__(self, report_paths, parent=None):
        super().__init__(parent)
        self._paths = list(report_paths)
        self.setWindowTitle("TASS crashed during your last session")
        self.setModal(True)
        self.setMinimumWidth(480)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        n = len(self._paths)
        if n == 1:
            text = (
                "A report from the last crash was saved on this computer. It "
                "has not been sent. Would you like to review and send it now?"
            )
            review_label = "Review and send"
            delete_label = "Delete this report"
        else:
            text = (
                f"{n} crash reports from previous sessions were saved on this "
                "computer. They have not been sent. Would you like to review "
                "them now?"
            )
            review_label = "Review one by one"
            delete_label = "Delete all"
        body = QLabel(text)
        body.setWordWrap(True)
        layout.addWidget(body)

        self._stop_saving = QCheckBox("Stop saving reports for later review")
        layout.addWidget(self._stop_saving)

        layout.addStretch()
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        remind = QPushButton("Remind me next launch")
        remind.clicked.connect(self._on_remind)
        btn_row.addWidget(remind)

        delete = QPushButton(delete_label)
        delete.clicked.connect(self._on_delete)
        btn_row.addWidget(delete)

        review = QPushButton(review_label)
        review.setDefault(True)
        review.clicked.connect(self._on_review)
        btn_row.addWidget(review)

        layout.addLayout(btn_row)

    def _capture_checkbox(self):
        if self._stop_saving.isChecked():
            _settings().set(er.KEY_QUEUE_ON_CRASH, False)

    def _on_review(self):
        self._capture_checkbox()
        self.accept()
        for path in self._paths:
            _review_one(path, self.parent())

    def _on_delete(self):
        self._capture_checkbox()
        for path in self._paths:
            er.delete_queued(path)
        self.accept()

    def _on_remind(self):
        self._capture_checkbox()
        self.reject()  # leave files in the queue

    @staticmethod
    def maybe_show(parent=None) -> None:
        """Show touchpoint C if reminders are on and queued reports exist."""
        if not _settings().get(er.KEY_REMIND_POST_RESTART, er.DEFAULT_REMIND_POST_RESTART):
            return
        paths = er.list_queued()
        if not paths:
            return
        PostRestartDialog(paths, parent).exec()


# ----------------------------------------------------------------------
# Settings -> Privacy: queued-report manager
# ----------------------------------------------------------------------


class QueuedReportsDialog(QDialog):
    """Lists queued reports with view / send / delete controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Queued crash reports")
        self.setModal(True)
        self.setMinimumSize(460, 320)
        self._build_ui()
        self._reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(10)

        self._list = QListWidget()
        layout.addWidget(self._list)

        self._empty = QLabel("No crash reports are queued.")
        self._empty.setStyleSheet("color: #888888;")
        layout.addWidget(self._empty)

        btn_row = QHBoxLayout()
        for label, slot in (
            ("View / send", self._view_selected),
            ("Delete", self._delete_selected),
            ("Delete all", self._delete_all),
        ):
            b = QPushButton(label)
            b.clicked.connect(slot)
            btn_row.addWidget(b)
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def _reload(self):
        self._list.clear()
        paths = er.list_queued()
        for path in paths:
            item = QListWidgetItem(path.name)
            item.setData(Qt.UserRole, str(path))
            self._list.addItem(item)
        self._list.setVisible(bool(paths))
        self._empty.setVisible(not paths)

    def _selected_path(self):
        item = self._list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _view_selected(self):
        path = self._selected_path()
        if path:
            _review_one(path, self)
            self._reload()

    def _delete_selected(self):
        path = self._selected_path()
        if path:
            er.delete_queued(path)
            self._reload()

    def _delete_all(self):
        er.clear_queue()
        self._reload()
