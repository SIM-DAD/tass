"""
Tests for services/error_reporter.py — the policy-compliant crash reporter.

Covers the data contract (section 4), path redaction (4.3), the mailto:
composer (section 7), and the local queue (section 5). The three dialogs are
GUI and are smoke-tested manually; this suite covers the headless service
layer that the dialogs depend on.

Run with:  pytest tests/test_error_reporter.py -v
"""

import os
import sys
import urllib.parse

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services import error_reporter as er


SAMPLE_TRACEBACK = (
    'Traceback (most recent call last):\n'
    '  File "C:\\Users\\alexl\\Projects\\SIM-DAD\\tass\\core\\dictionary_engine.py", '
    'line 152, in analyze\n'
    '    score = self._compute_idf(t)\n'
    'ZeroDivisionError: float division by zero\n'
)


# ----------------------------------------------------------------------
# Data contract (section 4)
# ----------------------------------------------------------------------

def test_build_report_has_only_contract_fields():
    report = er.build_report(SAMPLE_TRACEBACK)
    expected = {
        "product_name", "product_version", "crash_timestamp", "traceback",
        "os_name", "os_version", "cpu_model", "ram_total_gb", "python_version",
    }
    assert set(report.__dataclass_fields__) == expected
    assert report.product_name == "TASS"
    assert isinstance(report.ram_total_gb, int)
    assert report.crash_timestamp.endswith("Z")
    assert "T" in report.crash_timestamp
    assert report.python_version  # always populated


# ----------------------------------------------------------------------
# Redaction (section 4.3)
# ----------------------------------------------------------------------

def test_redaction_strips_username_and_home_path():
    redacted = er.redact_paths(SAMPLE_TRACEBACK)
    assert "alexl" not in redacted
    assert "C:\\Users" not in redacted
    assert "<redacted-path>" in redacted


def test_redaction_keeps_filename_lineno_and_func():
    redacted = er.redact_paths(SAMPLE_TRACEBACK)
    assert "dictionary_engine.py" in redacted
    assert "line 152" in redacted
    assert "in analyze" in redacted
    assert "ZeroDivisionError" in redacted


def test_redaction_strips_path_inside_exception_message():
    tb = (
        'Traceback (most recent call last):\n'
        '  File "C:\\Users\\alexl\\app\\importer.py", line 9, in load\n'
        "FileNotFoundError: [Errno 2] No such file: 'C:\\Users\\alexl\\Documents\\secret.csv'\n"
    )
    redacted = er.redact_paths(tb)
    assert "alexl" not in redacted
    assert "secret.csv" not in redacted


def test_build_report_redacts_by_default():
    report = er.build_report(SAMPLE_TRACEBACK)
    assert "alexl" not in report.traceback
    assert "<redacted-path>" in report.traceback


# ----------------------------------------------------------------------
# Disclosure text + mailto composer (sections 4.4, 7)
# ----------------------------------------------------------------------

def test_format_report_text_shape():
    report = er.build_report(SAMPLE_TRACEBACK)
    text = er.format_report_text(report)
    assert text.startswith("Product: TASS")
    assert "Version:" in text
    assert "RAM:" in text
    assert "ZeroDivisionError" in text


def test_compose_mailto_addresses_per_product_inbox_with_encoded_body():
    report = er.build_report(SAMPLE_TRACEBACK)
    url = er.compose_mailto(report)
    assert url.startswith("mailto:support+tass@simdadllc.com?")
    query = urllib.parse.parse_qs(url.split("?", 1)[1])
    assert "TASS Crash Report" in query["subject"][0]
    assert "ZeroDivisionError" in query["body"][0]


# ----------------------------------------------------------------------
# Local queue (section 5)
# ----------------------------------------------------------------------

def test_queue_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(er, "_QUEUE_DIR", tmp_path / "crash-queue")
    assert er.list_queued() == []

    report = er.build_report(SAMPLE_TRACEBACK)
    path = er.queue_report(report)
    assert path is not None and path.exists()

    queued = er.list_queued()
    assert len(queued) == 1

    loaded = er.load_queued(queued[0])
    assert loaded is not None
    assert loaded.traceback == report.traceback
    assert loaded.product_name == "TASS"

    er.delete_queued(queued[0])
    assert er.list_queued() == []


def test_clear_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(er, "_QUEUE_DIR", tmp_path / "crash-queue")
    er.queue_report(er.build_report(SAMPLE_TRACEBACK))
    er.queue_report(er.build_report(SAMPLE_TRACEBACK + "\n# variant"))
    assert len(er.list_queued()) >= 1
    er.clear_queue()
    assert er.list_queued() == []


def test_queue_filename_format(tmp_path, monkeypatch):
    monkeypatch.setattr(er, "_QUEUE_DIR", tmp_path / "crash-queue")
    report = er.build_report(SAMPLE_TRACEBACK)
    path = er.queue_report(report)
    # YYYYMMDD-HHMMSS-<sha1prefix>.json
    name = path.name
    assert name.endswith(".json")
    stamp, _, rest = name.partition("-")
    assert len(stamp) == 8 and stamp.isdigit()
