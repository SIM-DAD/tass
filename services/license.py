"""
License service — manages trial signup, license key activation, and local license cache.
Integrates with Lemon Squeezy (key validation) and Supabase (machine activation records).
"""

from __future__ import annotations
import os
import json
import hashlib
import datetime
from dataclasses import dataclass
from typing import Optional


CACHE_FILE = os.path.join(os.path.expanduser("~"), ".tass_license.lcache")
TRIAL_DURATION_DAYS = 14
TRIAL_ROW_LIMIT = 500


@dataclass
class LicenseStatus:
    mode: str                      # "trial", "licensed", "expired", "none"
    tier: Optional[str] = None     # "individual", "team_5", "team_10"
    email: Optional[str] = None
    expires_at: Optional[str] = None
    trial_rows_remaining: Optional[int] = None

    @property
    def display_label(self) -> str:
        if self.mode == "licensed":
            return f"Licensed ({self.tier or 'Individual'})"
        if self.mode == "trial":
            remaining = ""
            if self.expires_at:
                try:
                    exp = datetime.datetime.fromisoformat(self.expires_at)
                    days = (exp - datetime.datetime.utcnow()).days
                    remaining = f" — {max(0, days)}d remaining"
                except Exception:
                    pass
            return f"Trial{remaining}"
        if self.mode == "expired":
            return "Trial Expired — View Only"
        return "Not Activated"


class LicenseService:
    """
    Manages reading/writing the local license cache and calling remote APIs.
    """

    def get_status(self) -> LicenseStatus:
        cache = self._read_cache()
        if not cache:
            return LicenseStatus(mode="none")

        mode = cache.get("mode", "none")
        expires_str = cache.get("expires_at")

        if expires_str:
            try:
                exp = datetime.datetime.fromisoformat(expires_str)
                if datetime.datetime.utcnow() > exp:
                    mode = "expired"
            except Exception:
                pass

        return LicenseStatus(
            mode=mode,
            tier=cache.get("tier"),
            email=cache.get("email"),
            expires_at=expires_str,
            trial_rows_remaining=(
                TRIAL_ROW_LIMIT if mode == "trial" else None
            ),
        )

    def start_trial(self, email: str) -> LicenseStatus:
        """Register a trial via Supabase. Falls back to offline trial if network unavailable."""
        expires_at = (
            datetime.datetime.utcnow() + datetime.timedelta(days=TRIAL_DURATION_DAYS)
        ).isoformat()

        try:
            from services.supabase_client import SupabaseClient
            client = SupabaseClient()
            result = client.create_trial(email, expires_at)
            trial_key = result.get("trial_key", "offline")
        except Exception:
            trial_key = "offline"

        cache = {
            "mode": "trial",
            "email": email,
            "trial_key": trial_key,
            "expires_at": expires_at,
            "machine_id": _machine_fingerprint(),
        }
        self._write_cache(cache)
        return self.get_status()

    def activate_license(self, license_key: str) -> LicenseStatus:
        """Validate key with Lemon Squeezy and register machine with Supabase."""
        try:
            from services.lemon_squeezy_client import LemonSqueezyClient
            ls = LemonSqueezyClient()
            key_data = ls.validate_key(license_key)
        except Exception as exc:
            raise RuntimeError(f"License validation failed: {exc}") from exc

        if not key_data.get("valid"):
            raise RuntimeError(key_data.get("error", "Invalid license key."))

        expires_at = key_data.get("expires_at")
        tier = key_data.get("tier", "individual")

        try:
            from services.supabase_client import SupabaseClient
            SupabaseClient().activate_machine(
                license_key=license_key,
                machine_fingerprint=_machine_fingerprint(),
                tass_version=_tass_version(),
            )
        except Exception:
            pass  # Non-fatal; local cache is still written

        cache = {
            "mode": "licensed",
            "license_key": license_key,
            "tier": tier,
            "expires_at": expires_at,
            "machine_id": _machine_fingerprint(),
        }
        self._write_cache(cache)
        return self.get_status()

    def is_trial_row_limit_exceeded(self, row_count: int) -> bool:
        status = self.get_status()
        if status.mode == "trial":
            return row_count > TRIAL_ROW_LIMIT
        return False

    # ------------------------------------------------------------------
    # Local cache helpers (plain JSON for now; encrypt in future sprint)
    # ------------------------------------------------------------------

    def _read_cache(self) -> Optional[dict]:
        if not os.path.exists(CACHE_FILE):
            return None
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def _write_cache(self, data: dict):
        with open(CACHE_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _machine_fingerprint() -> str:
    """Hashed hardware ID (simplified; full implementation uses CPU/disk/MAC)."""
    import platform
    raw = f"{platform.node()}{platform.machine()}{platform.processor()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _tass_version() -> str:
    try:
        from app import TASS_VERSION
        return TASS_VERSION
    except Exception:
        return "unknown"
