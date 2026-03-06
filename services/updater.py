"""
Update checker — checks GitHub Releases API for new TASS versions.
Runs silently in background at startup (v1.1 feature, stubbed for v1.0).
"""

from __future__ import annotations
import threading
from typing import Optional, Callable

GITHUB_RELEASES_URL = "https://api.github.com/repos/simdadllc/tass/releases/latest"
CHECK_TIMEOUT = 5  # seconds


class UpdateChecker:
    """
    Checks for updates in a daemon thread.
    Calls on_update_available(latest_version, release_url, changelog) if a newer version is found.
    """

    def __init__(self, current_version: str):
        self.current_version = current_version
        self._thread: Optional[threading.Thread] = None

    def check_async(self, on_update_available: Callable[[str, str, str], None]):
        """Start a background thread to check for updates."""
        self._thread = threading.Thread(
            target=self._check,
            args=(on_update_available,),
            daemon=True,
        )
        self._thread.start()

    def _check(self, callback: Callable):
        try:
            import requests
            resp = requests.get(GITHUB_RELEASES_URL, timeout=CHECK_TIMEOUT)
            if resp.status_code != 200:
                return
            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            release_url = data.get("html_url", "")
            changelog = data.get("body", "")

            if latest and _version_newer(latest, self.current_version):
                callback(latest, release_url, changelog)
        except Exception:
            pass  # Update check is non-critical; fail silently


def _version_newer(latest: str, current: str) -> bool:
    """Compare semver strings. Returns True if latest > current."""
    try:
        def parse(v):
            return tuple(int(x) for x in v.split(".")[:3])
        return parse(latest) > parse(current)
    except Exception:
        return False
