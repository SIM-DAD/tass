"""
Lemon Squeezy client — manages license activation/validation via the LS API.

LS license endpoints use application/x-www-form-urlencoded, not JSON API.
Flow:
  1. activate_machine(key, instance_name) → instance_id  (on first activation)
  2. validate_key(key, instance_id)                      (on subsequent launches)
  3. deactivate_machine(key, instance_id)                (on user request / seat swap)
"""

from __future__ import annotations
import os
import requests
from typing import Dict, Any, Optional

LS_API_URL = "https://api.lemonsqueezy.com/v1"
# Load from environment; fall back to the project key only in dev builds.
# IMPORTANT: set TASS_LS_API_KEY in the build environment / .env — never ship
# a production key as source-code default.
LS_API_KEY = os.environ.get("TASS_LS_API_KEY", "")

TIMEOUT = 10


class LemonSqueezyClient:
    def __init__(self):
        self.api_key = LS_API_KEY
        if not self.api_key:
            raise RuntimeError(
                "Lemon Squeezy not configured. Set TASS_LS_API_KEY environment variable."
            )

    @property
    def _headers(self) -> Dict[str, str]:
        """Headers for license endpoints (form-encoded, not JSON API)."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Activation (call once per machine — returns instance_id to cache)
    # ------------------------------------------------------------------

    def activate_machine(self, license_key: str, instance_name: str) -> Dict[str, Any]:
        """
        Activate a license key for this machine.
        Returns: {activated: bool, instance_id: str|None, tier: str, expires_at: str|None, error: str|None}
        """
        resp = requests.post(
            f"{LS_API_URL}/licenses/activate",
            data={"license_key": license_key, "instance_name": instance_name},
            headers=self._headers,
            timeout=TIMEOUT,
        )

        if resp.status_code in (400, 422):
            body = _safe_json(resp)
            return {"activated": False, "instance_id": None,
                    "error": body.get("error", "Activation failed.")}

        resp.raise_for_status()
        data = resp.json()

        meta = data.get("meta", {})
        instance = data.get("instance", {})
        license_obj = data.get("license_key", {})

        return {
            "activated": data.get("activated", False),
            "instance_id": instance.get("id"),
            "tier": _map_variant_to_tier(meta.get("variant_name", "")),
            "expires_at": license_obj.get("expires_at"),
            "error": data.get("error"),
        }

    # ------------------------------------------------------------------
    # Validation (use cached instance_id for per-machine validation)
    # ------------------------------------------------------------------

    def validate_key(self, license_key: str, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a license key (optionally scoped to a cached instance_id).
        Returns: {valid: bool, tier: str, expires_at: str|None, error: str|None}
        """
        payload: Dict[str, str] = {"license_key": license_key}
        if instance_id:
            payload["instance_id"] = instance_id

        resp = requests.post(
            f"{LS_API_URL}/licenses/validate",
            data=payload,
            headers=self._headers,
            timeout=TIMEOUT,
        )

        if resp.status_code == 404:
            return {"valid": False, "error": "License key not found."}
        if resp.status_code == 400:
            return {"valid": False, "error": "Invalid license key format."}

        resp.raise_for_status()
        data = resp.json()

        license_obj = data.get("license_key", {})
        status = license_obj.get("status")
        valid = data.get("valid", False)
        meta = data.get("meta", {})
        tier = _map_variant_to_tier(meta.get("variant_name", "individual"))
        expires_at = license_obj.get("expires_at")

        return {
            "valid": valid,
            "tier": tier,
            "expires_at": expires_at,
            "status": status,
            "error": None if valid else (data.get("error") or f"License status: {status}"),
        }

    # ------------------------------------------------------------------
    # Deactivation
    # ------------------------------------------------------------------

    def deactivate_machine(self, license_key: str, instance_id: str) -> bool:
        """Deactivate a machine instance to free up a seat."""
        resp = requests.post(
            f"{LS_API_URL}/licenses/deactivate",
            data={"license_key": license_key, "instance_id": instance_id},
            headers=self._headers,
            timeout=TIMEOUT,
        )
        return resp.status_code == 200


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _map_variant_to_tier(variant_name: str) -> str:
    v = variant_name.lower()
    if "team" in v and "10" in v:
        return "team_10"
    if "team" in v and "5" in v:
        return "team_5"
    return "individual"


def _safe_json(resp: requests.Response) -> dict:
    try:
        return resp.json()
    except Exception:
        return {}
