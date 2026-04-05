"""
License service — manages trial signup, license key activation, and local license cache.
Uses Gumroad License Verification API. No external dependencies (urllib only).

Gumroad endpoint: POST https://api.gumroad.com/v2/licenses/verify
  - product_id + license_key (form-encoded, no auth required)
  - increment_uses_count: "true" on activation, "false" on check
  - Response: {success, uses, purchase: {email, product_name, variants, refunded, chargebacked}}

Device limits enforced client-side via uses count:
  - Individual: 1 device
  - Team 5: 5 devices
  - Team 10: 10 devices
"""

from __future__ import annotations
import hashlib
import json
import logging
import datetime
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import platformdirs

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(platformdirs.user_config_dir("TASS", appauthor=False))
LICENSE_PATH = CONFIG_DIR / "license.json"
GUMROAD_VERIFY = "https://api.gumroad.com/v2/licenses/verify"
TIMEOUT = 10

# Gumroad product_id — set after publishing.
PRODUCT_ID = ""  # TODO: fill after Gumroad product is published

TRIAL_DURATION_DAYS = 30
TRIAL_ROW_LIMIT = 500
GRACE_DAYS = 14

# Device limits per Gumroad Membership tier
TIER_MAX_USES = {"academic": 2, "professional": 2, "lab": 10, "department": 50}
DEFAULT_MAX_USES = 2


@dataclass
class LicenseStatus:
    mode: str                      # "trial", "licensed", "expired", "lapsed", "none"
    tier: Optional[str] = None     # "academic", "professional", "lab", "department"
    email: Optional[str] = None
    expires_at: Optional[str] = None
    trial_rows_remaining: Optional[int] = None

    @property
    def display_label(self) -> str:
        if self.mode == "licensed":
            return f"Licensed ({self.tier or 'Academic'})"
        if self.mode == "trial":
            remaining = ""
            if self.expires_at:
                try:
                    exp = datetime.datetime.fromisoformat(self.expires_at)
                    if exp.tzinfo is None:
                        exp = exp.replace(tzinfo=datetime.timezone.utc)
                    days = (exp - datetime.datetime.now(datetime.timezone.utc)).days
                    remaining = f" — {max(0, days)}d remaining"
                except Exception:
                    pass
            return f"Trial{remaining}"
        if self.mode == "expired":
            return "Trial Expired — View Only"
        if self.mode == "lapsed":
            return "Subscription Lapsed — Renew"
        return "Not Activated"


class LicenseService:
    """
    Manages reading/writing the local license cache and calling Gumroad API.
    """

    def get_status(self) -> LicenseStatus:
        cache = self._read_cache()
        if not cache:
            return LicenseStatus(mode="none")

        mode = cache.get("mode", "none")
        expires_str = cache.get("expires_at")

        if mode == "trial" and expires_str:
            try:
                exp = datetime.datetime.fromisoformat(expires_str)
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=datetime.timezone.utc)
                if datetime.datetime.now(datetime.timezone.utc) > exp:
                    mode = "expired"
            except Exception:
                pass

        # Lapsed subscriptions block analysis just like expired trials
        if mode == "lapsed":
            return LicenseStatus(mode="lapsed", email=cache.get("email"))

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
        """Register a local trial (no remote calls)."""
        expires_at = (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=TRIAL_DURATION_DAYS)
        ).isoformat()

        cache = {
            "mode": "trial",
            "email": email,
            "expires_at": expires_at,
            "machine_id": _machine_fingerprint(),
        }
        self._write_cache(cache)
        return self.get_status()

    def activate_license(self, license_key: str) -> LicenseStatus:
        """Activate key with Gumroad and cache locally."""
        license_key = license_key.strip()

        try:
            data = _gumroad_post({
                "product_id":           PRODUCT_ID,
                "license_key":          license_key,
                "increment_uses_count": "true",
            })
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise RuntimeError("License key not found. Check the key in your receipt email.")
            raise RuntimeError("Could not reach the activation server. Check your internet connection.")
        except urllib.error.URLError:
            raise RuntimeError("Could not reach the activation server. Check your internet connection.")
        except Exception as exc:
            raise RuntimeError(f"License activation failed: {exc}") from exc

        if not data.get("success"):
            raise RuntimeError(data.get("message", "Invalid license key."))

        purchase = data.get("purchase", {})

        if purchase.get("refunded") or purchase.get("chargebacked"):
            raise RuntimeError("This purchase has been refunded. Contact hello@simdadllc.com for help.")

        # Subscription status check
        if _is_subscription_lapsed(purchase):
            raise RuntimeError(
                "Your subscription is no longer active.\n\n"
                "If you've renewed, it may take a few minutes to update. "
                "Try again shortly, or contact hello@simdadllc.com."
            )

        variant = purchase.get("variants", "")
        tier = _map_variant_to_tier(variant)
        max_uses = TIER_MAX_USES.get(tier, DEFAULT_MAX_USES)
        uses = data.get("uses", 0)

        if uses > max_uses:
            raise RuntimeError(
                f"This key has reached its activation limit ({max_uses} devices). "
                "Contact hello@simdadllc.com to reset it."
            )

        cache = {
            "mode": "licensed",
            "license_key": license_key,
            "tier": tier,
            "email": purchase.get("email", ""),
            "uses": uses,
            "max_uses": max_uses,
            "machine_id": _machine_fingerprint(),
            "activated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "last_validated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        self._write_cache(cache)
        return self.get_status()

    def check_online(self) -> LicenseStatus:
        """Re-validate a licensed key with Gumroad (non-incrementing)."""
        cache = self._read_cache()
        if not cache or cache.get("mode") != "licensed":
            return self.get_status()

        try:
            data = _gumroad_post({
                "product_id":           PRODUCT_ID,
                "license_key":          cache["license_key"],
                "increment_uses_count": "false",
            })

            if not data.get("success"):
                cache["mode"] = "none"
                self._write_cache(cache)
                return LicenseStatus(mode="none")

            purchase = data.get("purchase", {})
            if purchase.get("refunded") or purchase.get("chargebacked"):
                cache["mode"] = "none"
                self._write_cache(cache)
                return LicenseStatus(mode="none")

            # Subscription lapsed (cancelled past billing period, or failed payment past grace)
            if _is_subscription_lapsed(purchase):
                cache["mode"] = "lapsed"
                self._write_cache(cache)
                return LicenseStatus(mode="lapsed", email=cache.get("email"))

            cache["last_validated"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self._write_cache(cache)

        except Exception:
            # Offline — check grace period
            last_str = cache.get("last_validated") or cache.get("activated_at", "")
            if last_str:
                try:
                    last = datetime.datetime.fromisoformat(last_str)
                    if last.tzinfo is None:
                        last = last.replace(tzinfo=datetime.timezone.utc)
                    if datetime.datetime.now(datetime.timezone.utc) - last > datetime.timedelta(days=GRACE_DAYS):
                        cache["mode"] = "none"
                        self._write_cache(cache)
                        return LicenseStatus(mode="none")
                except Exception:
                    pass

        return self.get_status()

    def is_trial_row_limit_exceeded(self, row_count: int) -> bool:
        status = self.get_status()
        if status.mode == "trial":
            return row_count > TRIAL_ROW_LIMIT
        return False

    # ------------------------------------------------------------------
    # Local cache helpers
    # ------------------------------------------------------------------

    def _read_cache(self) -> Optional[dict]:
        if not LICENSE_PATH.exists():
            return None
        try:
            with LICENSE_PATH.open("r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    def _write_cache(self, data: dict):
        LICENSE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LICENSE_PATH.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _gumroad_post(params: dict) -> dict:
    """POST form-encoded params to Gumroad verify endpoint."""
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(GUMROAD_VERIFY, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _machine_fingerprint() -> str:
    """SHA-256 of a stable hardware identifier."""
    raw = _raw_machine_id()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _raw_machine_id() -> str:
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
                0,
                winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
            )
            value, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
            return value
        except Exception:
            pass
    elif sys.platform == "darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True, text=True, timeout=5,
            )
            for line in result.stdout.splitlines():
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        except Exception:
            pass
    else:
        try:
            return open("/etc/machine-id").read().strip()
        except Exception:
            pass
    import socket
    return socket.gethostname()


def _map_variant_to_tier(variant_name: str) -> str:
    v = (variant_name or "").lower()
    if "department" in v:
        return "department"
    if "lab" in v:
        return "lab"
    if "professional" in v:
        return "professional"
    if "academic" in v:
        return "academic"
    # Legacy fallback
    if "team" in v and "10" in v:
        return "department"
    if "team" in v and "5" in v:
        return "lab"
    return "academic"


def _is_subscription_lapsed(purchase: dict) -> bool:
    """Check if a Gumroad subscription has lapsed.

    Gumroad subscription fields:
      - subscription_cancelled_at: ISO timestamp when user cancelled (null if active)
      - subscription_failed_at:   ISO timestamp when payment failed (null if OK)
      - subscription_ended_at:    ISO timestamp when billing period actually ends

    Policy:
      - Cancelled: access continues until subscription_ended_at (end of billing period).
        If subscription_ended_at is missing, allow GRACE_DAYS from cancellation.
      - Failed payment: allow GRACE_DAYS from failure date to fix payment method.
      - Active (neither cancelled nor failed): not lapsed.
    """
    now = datetime.datetime.now(datetime.timezone.utc)

    # Check for cancellation
    cancelled_str = purchase.get("subscription_cancelled_at")
    if cancelled_str:
        ended_str = purchase.get("subscription_ended_at")
        if ended_str:
            # Access until end of billing period
            try:
                ended = datetime.datetime.fromisoformat(ended_str.replace("Z", "+00:00"))
                if ended.tzinfo is None:
                    ended = ended.replace(tzinfo=datetime.timezone.utc)
                return now > ended
            except (ValueError, TypeError):
                pass
        # No end date — use grace period from cancellation
        try:
            cancelled = datetime.datetime.fromisoformat(cancelled_str.replace("Z", "+00:00"))
            if cancelled.tzinfo is None:
                cancelled = cancelled.replace(tzinfo=datetime.timezone.utc)
            return now > cancelled + datetime.timedelta(days=GRACE_DAYS)
        except (ValueError, TypeError):
            return True  # Can't parse date — treat as lapsed

    # Check for failed payment
    failed_str = purchase.get("subscription_failed_at")
    if failed_str:
        try:
            failed = datetime.datetime.fromisoformat(failed_str.replace("Z", "+00:00"))
            if failed.tzinfo is None:
                failed = failed.replace(tzinfo=datetime.timezone.utc)
            return now > failed + datetime.timedelta(days=GRACE_DAYS)
        except (ValueError, TypeError):
            return True  # Can't parse date — treat as lapsed

    return False  # Active subscription
