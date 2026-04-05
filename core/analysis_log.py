"""
Analysis log — records timestamped analytical decisions for reproducibility.

Each entry is a plain-text line with ISO timestamp + description.
The log is per-session (not persisted across app restarts unless saved).
Can be exported as plain text or embedded in .tass project files.
"""

from __future__ import annotations
import datetime
from typing import List


class AnalysisLog:
    """Append-only log of analytical decisions with timestamps."""

    _instance: AnalysisLog | None = None

    def __init__(self):
        self._entries: List[str] = []

    @classmethod
    def instance(cls) -> AnalysisLog:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> AnalysisLog:
        cls._instance = cls()
        return cls._instance

    def log(self, message: str) -> None:
        """Append a timestamped entry."""
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self._entries.append(f"[{ts}] {message}")

    def log_section(self, title: str) -> None:
        """Append a section divider."""
        self._entries.append(f"\n--- {title} ---")

    @property
    def entries(self) -> List[str]:
        return list(self._entries)

    @property
    def is_empty(self) -> bool:
        return len(self._entries) == 0

    def as_text(self) -> str:
        """Return the full log as a plain-text string."""
        header = (
            "TASS Analysis Log\n"
            "=================\n"
            "This log records all analytical decisions made during the session.\n"
            "Timestamps are in UTC.\n\n"
        )
        return header + "\n".join(self._entries) + "\n"

    def clear(self) -> None:
        self._entries.clear()
