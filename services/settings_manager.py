"""
Settings manager — replaces QSettings with a portable JSON file.

Stores user preferences in a platform-appropriate config directory:
  Windows: %APPDATA%/TASS/settings.json
  macOS:   ~/Library/Application Support/TASS/settings.json
  Linux:   ~/.config/TASS/settings.json

Thread-safe for reads; writes are atomic (write-to-temp + rename).
"""

from __future__ import annotations
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, List, Optional

import platformdirs

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(platformdirs.user_config_dir("TASS", appauthor=False))
_SETTINGS_PATH = _CONFIG_DIR / "settings.json"


class SettingsManager:
    """Simple JSON-backed key-value store for user preferences."""

    _instance: Optional[SettingsManager] = None

    def __init__(self):
        self._data: dict = {}
        self._load()

    @classmethod
    def instance(cls) -> SettingsManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Read a value. Supports dotted keys: 'viz.palette'."""
        parts = key.split(".")
        obj = self._data
        for p in parts[:-1]:
            obj = obj.get(p, {})
            if not isinstance(obj, dict):
                return default
        return obj.get(parts[-1], default)

    def set(self, key: str, value: Any) -> None:
        """Write a value and flush to disk. Supports dotted keys."""
        parts = key.split(".")
        obj = self._data
        for p in parts[:-1]:
            if p not in obj or not isinstance(obj[p], dict):
                obj[p] = {}
            obj = obj[p]
        obj[parts[-1]] = value
        self._save()

    def get_list(self, key: str, default: Optional[List] = None) -> List:
        val = self.get(key, default or [])
        return val if isinstance(val, list) else (default or [])

    def get_bytes(self, key: str) -> Optional[bytes]:
        """Read a base64-encoded bytes value (for Qt geometry)."""
        import base64
        val = self.get(key)
        if val and isinstance(val, str):
            try:
                return base64.b64decode(val)
            except Exception:
                return None
        return None

    def set_bytes(self, key: str, data: bytes) -> None:
        """Write bytes as base64 string."""
        import base64
        self.set(key, base64.b64encode(data).decode("ascii"))

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if not _SETTINGS_PATH.exists():
            self._data = {}
            return
        try:
            with _SETTINGS_PATH.open("r", encoding="utf-8") as fh:
                self._data = json.load(fh)
        except Exception as exc:
            logger.warning("Failed to load settings: %s", exc)
            self._data = {}

    def _save(self):
        _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        try:
            # Atomic write: temp file + rename
            fd, tmp = tempfile.mkstemp(dir=str(_CONFIG_DIR), suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(self._data, fh, indent=2, default=str)
                # On Windows, rename fails if target exists — remove first
                if _SETTINGS_PATH.exists():
                    _SETTINGS_PATH.unlink()
                os.rename(tmp, str(_SETTINGS_PATH))
            except Exception:
                # Clean up temp file on failure
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except Exception as exc:
            logger.warning("Failed to save settings: %s", exc)
