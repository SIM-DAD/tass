"""
Error reporter — sends opt-in crash reports via email (SMTP).
No user text or data is ever included; only: traceback, TASS version, OS, hardware.
"""

from __future__ import annotations
import platform
import os
import smtplib
import datetime
from email.message import EmailMessage


REPORT_TO = "support@simdadllc.com"  # Update with real support address
SMTP_HOST = "smtp.gmail.com"          # Update with real SMTP config
SMTP_PORT = 587
SMTP_USER = ""                        # Set via environment variable TASS_SMTP_USER
SMTP_PASS = ""                        # Set via environment variable TASS_SMTP_PASS


class ErrorReporter:
    def send(self, traceback_str: str) -> bool:
        """
        Send a crash report. Returns True on success, False on failure.
        Never raises.
        """
        try:
            return self._send_email(traceback_str)
        except Exception:
            return False

    def _send_email(self, traceback_str: str) -> bool:
        smtp_user = os.environ.get("TASS_SMTP_USER", SMTP_USER)
        smtp_pass = os.environ.get("TASS_SMTP_PASS", SMTP_PASS)

        if not smtp_user or not smtp_pass:
            # No SMTP credentials configured — log locally instead
            self._log_locally(traceback_str)
            return False

        body = self._build_report(traceback_str)
        msg = EmailMessage()
        msg["Subject"] = f"TASS Crash Report — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        msg["From"] = smtp_user
        msg["To"] = REPORT_TO
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)

        return True

    def _build_report(self, traceback_str: str) -> str:
        version = "1.0.0"

        import psutil
        try:
            ram_gb = psutil.virtual_memory().total / (1024 ** 3)
            cpu_cores = psutil.cpu_count(logical=False)
        except Exception:
            ram_gb = "unknown"
            cpu_cores = "unknown"

        return (
            f"TASS Crash Report\n"
            f"{'=' * 60}\n"
            f"TASS Version : {version}\n"
            f"Timestamp    : {datetime.datetime.utcnow().isoformat()}Z\n"
            f"OS           : {platform.platform()}\n"
            f"Python       : {platform.python_version()}\n"
            f"CPU          : {platform.processor()} ({cpu_cores} cores)\n"
            f"RAM          : {ram_gb:.1f} GB\n"
            f"{'=' * 60}\n\n"
            f"Traceback:\n{traceback_str}\n"
            f"\n[No user data, text content, or file contents are included.]\n"
        )

    def _log_locally(self, traceback_str: str) -> None:
        log_dir = os.path.join(os.path.expanduser("~"), ".tass_logs")
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(log_dir, f"crash_{ts}.log")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self._build_report(traceback_str))
