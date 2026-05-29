"""
Error reporter — builds policy-compliant crash reports and supports manual,
user-initiated submission through the customer's own mail client (mailto:).

Complies with the SIM DAD LLC Error-Reporting Policy
(C:/life-os/llc/policies/error-reporting-policy.md):

  - No SMTP. No third-party error-tracking SDK. No telemetry. No background
    uploader. Nothing leaves the machine without an explicit user Send click.
  - Fixed data contract (section 4): traceback + product version + OS +
    hardware specs only. No documents, no analysis data, no PII, no paths.
  - File paths in the traceback are redacted to "<redacted-path>" before the
    report is built, so what the user reviews is exactly what gets sent.
  - Reports are queued locally only (section 5); the queue is surfaced on the
    next launch by touchpoint C and is never auto-sent.

This module is UI-free. The three touchpoint dialogs (ui/crash_dialogs.py)
call build_report(), compose_mailto(), and the queue helpers; the actual
"open the mail client" / "copy" / "save" actions live in the dialog layer.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import re
import urllib.parse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

import platformdirs

PRODUCT_NAME = "TASS"
# Per-product support inbox (policy section 7). Plus-addressing lands in
# support@simdadllc.com and is filtered to a per-product label.
SUPPORT_INBOX = "support+tass@simdadllc.com"

# Queue directory (policy section 5):
#   Windows: %LOCALAPPDATA%\TASS\crash-queue\
#   macOS:   ~/Library/Application Support/TASS/crash-queue/
#   Linux:   ~/.local/share/TASS/crash-queue/
_QUEUE_DIR = Path(platformdirs.user_data_dir(PRODUCT_NAME, appauthor=False)) / "crash-queue"

# Keep the mailto body within length limits common to mail clients. The full
# report is always available via the dialog's Copy / Save buttons.
_MAILTO_BODY_LIMIT = 1800


# ----------------------------------------------------------------------
# Settings keys (policy section 6). Defaults are the policy defaults.
# ----------------------------------------------------------------------

KEY_PROMPT_ON_CRASH = "crash_reporting.prompt_on_crash"
KEY_QUEUE_ON_CRASH = "crash_reporting.queue_on_crash"
KEY_REMIND_POST_RESTART = "crash_reporting.remind_post_restart"
KEY_FIRST_LAUNCH_PROMPT_SHOWN = "crash_reporting.first_launch_prompt_shown"

DEFAULT_PROMPT_ON_CRASH = True
DEFAULT_QUEUE_ON_CRASH = True
DEFAULT_REMIND_POST_RESTART = True


# ----------------------------------------------------------------------
# Path redaction (policy section 4.3 + 4.4)
# ----------------------------------------------------------------------

# Match a traceback frame's file path: File "<path>"
_FILE_FRAME_RE = re.compile(r'File "(?P<path>[^"]+)"')
# Absolute Windows drive paths (C:\...), UNC paths (\\server\...), and POSIX
# home paths (/Users/... or /home/...) that may appear in exception messages.
_WIN_PATH_RE = re.compile(r'[A-Za-z]:\\[^\s"\'<>|]+')
_UNC_PATH_RE = re.compile(r'\\\\[^\s"\'<>|]+')
_POSIX_HOME_RE = re.compile(r'/(?:home|Users)/[^\s"\'<>|:]+')


def redact_paths(text: str) -> str:
    """Strip absolute file paths from a traceback while keeping it diagnostic.

    Traceback frames keep the source filename (e.g.
    ``File "<redacted-path>/dictionary_engine.py"``) so the report still points
    at the failing module, but the directory prefix — which can carry the
    username, home directory, or document paths — is removed. Any remaining
    absolute path elsewhere in the text (e.g. inside an exception message such
    as a FileNotFoundError) is replaced wholesale with ``<redacted-path>``.
    """

    def _frame_sub(match: "re.Match[str]") -> str:
        path = match.group("path")
        base = os.path.basename(path.replace("\\", "/")) or "<unknown>"
        return f'File "<redacted-path>/{base}"'

    # Frames first (they preserve the basename), then any other absolute paths.
    text = _FILE_FRAME_RE.sub(_frame_sub, text)
    text = _WIN_PATH_RE.sub("<redacted-path>", text)
    text = _UNC_PATH_RE.sub("<redacted-path>", text)
    text = _POSIX_HOME_RE.sub("<redacted-path>", text)
    return text


# ----------------------------------------------------------------------
# Report model (policy section 4 data contract)
# ----------------------------------------------------------------------


@dataclass
class CrashReport:
    """The fixed crash-report schema. Any field outside this is a violation.

    TASS does not use the GPU, so the optional gpu_model / vram_total_gb /
    display_resolution fields from policy 4.2 are intentionally omitted.
    """

    product_name: str
    product_version: str
    crash_timestamp: str  # UTC ISO8601, e.g. "2026-05-29T18:42:10Z"
    traceback: str        # already redacted
    os_name: str
    os_version: str
    cpu_model: str
    ram_total_gb: int
    python_version: Optional[str] = None

    def traceback_sha1(self) -> str:
        return hashlib.sha1(self.traceback.encode("utf-8", "replace")).hexdigest()


def _product_version() -> str:
    """Resolve the running TASS version without coupling to app.py at import."""
    try:
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None and app.applicationVersion():
            return app.applicationVersion()
    except Exception:
        pass
    return "1.0.0"


def _ram_total_gb() -> int:
    try:
        import psutil

        return round(psutil.virtual_memory().total / (1024 ** 3))
    except Exception:
        return 0


def build_report(traceback_str: str, *, redact: bool = True) -> CrashReport:
    """Build a section-4-compliant CrashReport from a traceback string.

    Redaction happens here, before the report is ever rendered, so the dialog
    shows exactly what would be sent.
    """
    tb = redact_paths(traceback_str) if redact else traceback_str
    now = datetime.datetime.now(datetime.timezone.utc)
    return CrashReport(
        product_name=PRODUCT_NAME,
        product_version=_product_version(),
        crash_timestamp=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        traceback=tb.rstrip(),
        os_name=platform.system() or "unknown",
        os_version=platform.version() or "unknown",
        cpu_model=(platform.processor() or platform.machine() or "unknown"),
        ram_total_gb=_ram_total_gb(),
        python_version=platform.python_version(),
    )


def format_report_text(report: CrashReport) -> str:
    """Render the canonical plaintext disclosure (matches policy section 4.4).

    This is the exact text shown in the dialog AND used as the email body, so
    review-equals-send holds.
    """
    ts = report.crash_timestamp.replace("T", " ").replace("Z", " UTC")
    lines = [
        f"Product: {report.product_name}",
        f"Version: {report.product_version}",
        f"Crash time: {ts}",
        "",
        f"OS: {report.os_name} {report.os_version}",
        f"CPU: {report.cpu_model}",
        f"RAM: {report.ram_total_gb} GB",
    ]
    if report.python_version:
        lines.append(f"Python: {report.python_version}")
    lines += ["", report.traceback.rstrip()]
    return "\n".join(lines)


def compose_mailto(report: CrashReport) -> str:
    """Build a mailto: URL pre-populating subject + body to the support inbox."""
    subject = f"{report.product_name} Crash Report — {report.crash_timestamp}"
    body = format_report_text(report)
    if len(body) > _MAILTO_BODY_LIMIT:
        body = (
            body[:_MAILTO_BODY_LIMIT]
            + "\n\n[Report truncated for email. Use \"Copy report to clipboard\" "
            "in the dialog to attach the full report.]"
        )
    query = urllib.parse.urlencode(
        {"subject": subject, "body": body},
        quote_via=urllib.parse.quote,
    )
    return f"mailto:{SUPPORT_INBOX}?{query}"


# ----------------------------------------------------------------------
# Local queue (policy section 5) — the only persistent state besides settings.
# ----------------------------------------------------------------------


def _queue_dir() -> Path:
    _QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    return _QUEUE_DIR


def _queue_filename(report: CrashReport) -> str:
    # YYYYMMDD-HHMMSS-<sha1-prefix>.json
    stamp = (
        report.crash_timestamp.replace("-", "")
        .replace(":", "")
        .replace("T", "-")
        .rstrip("Z")
    )
    return f"{stamp}-{report.traceback_sha1()[:12]}.json"


def queue_report(report: CrashReport) -> Optional[Path]:
    """Persist a report to the local queue for review on next launch.

    Never raises; returns the path written or None on failure.
    """
    try:
        path = _queue_dir() / _queue_filename(report)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(asdict(report), fh, indent=2)
        return path
    except Exception:
        return None


def list_queued() -> List[Path]:
    if not _QUEUE_DIR.exists():
        return []
    return sorted(_QUEUE_DIR.glob("*.json"))


def load_queued(path) -> Optional[CrashReport]:
    try:
        with Path(path).open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        fields = CrashReport.__dataclass_fields__
        return CrashReport(**{k: data.get(k) for k in fields})
    except Exception:
        return None


def delete_queued(path) -> None:
    try:
        Path(path).unlink()
    except OSError:
        pass


def clear_queue() -> None:
    for path in list_queued():
        delete_queued(path)
