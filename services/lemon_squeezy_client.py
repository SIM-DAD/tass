"""
Lemon Squeezy client — validates license keys via the LS API.
"""

from __future__ import annotations
import os
import requests
from typing import Dict, Any

LS_API_URL = "https://api.lemonsqueezy.com/v1"
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
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
        }

    def validate_key(self, license_key: str) -> Dict[str, Any]:
        """
        Validate a license key against Lemon Squeezy.
        Returns: {valid: bool, tier: str, expires_at: str|None, error: str|None}
        """
        resp = requests.post(
            f"{LS_API_URL}/licenses/validate",
            json={"license_key": {"key": license_key}},
            headers=self._headers,
            timeout=TIMEOUT,
        )

        if resp.status_code == 404:
            return {"valid": False, "error": "License key not found."}
        if resp.status_code == 400:
            return {"valid": False, "error": "Invalid license key format."}

        resp.raise_for_status()
        data = resp.json()

        # Parse LS response structure
        license_obj = data.get("data", {}).get("attributes", {})
        status = license_obj.get("status")
        valid = status == "active"

        meta = data.get("meta", {})
        variant_name = meta.get("variant_name", "individual")
        tier = _map_variant_to_tier(variant_name)
        expires_at = license_obj.get("expires_at")

        return {
            "valid": valid,
            "tier": tier,
            "expires_at": expires_at,
            "status": status,
            "error": None if valid else f"License status: {status}",
        }

    def deactivate_machine(self, license_key: str, instance_id: str) -> bool:
        """Deactivate a machine to free up a seat."""
        resp = requests.post(
            f"{LS_API_URL}/licenses/deactivate",
            json={
                "license_key": {"key": license_key},
                "instance_id": instance_id,
            },
            headers=self._headers,
            timeout=TIMEOUT,
        )
        return resp.status_code == 200


def _map_variant_to_tier(variant_name: str) -> str:
    v = variant_name.lower()
    if "team" in v and "10" in v:
        return "team_10"
    if "team" in v and "5" in v:
        return "team_5"
    return "individual"
