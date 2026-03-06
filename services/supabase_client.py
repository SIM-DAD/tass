"""
Supabase client — REST API calls for license and trial records.
Uses the Supabase HTTP API directly (no official Python SDK required).
"""

from __future__ import annotations
import os
import requests
from typing import Dict, Any

SUPABASE_URL = os.environ.get("TASS_SUPABASE_URL", "")        # e.g. https://xyz.supabase.co
SUPABASE_ANON_KEY = os.environ.get("TASS_SUPABASE_ANON_KEY", "")

TIMEOUT = 10  # seconds


class SupabaseClient:
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_ANON_KEY

        if not self.url or not self.key:
            raise RuntimeError(
                "Supabase not configured. "
                "Set TASS_SUPABASE_URL and TASS_SUPABASE_ANON_KEY environment variables."
            )

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }

    def create_trial(self, email: str, expires_at: str) -> Dict[str, Any]:
        """POST to Supabase edge function to create a trial record."""
        resp = requests.post(
            f"{self.url}/functions/v1/create-trial",
            json={"email": email, "expires_at": expires_at},
            headers=self._headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def activate_machine(self, license_key: str, machine_fingerprint: str, tass_version: str) -> Dict[str, Any]:
        """Register a machine activation for a license key."""
        resp = requests.post(
            f"{self.url}/functions/v1/activate-machine",
            json={
                "license_key": license_key,
                "machine_fingerprint": machine_fingerprint,
                "tass_version": tass_version,
            },
            headers=self._headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def get_license(self, license_key: str) -> Dict[str, Any]:
        """Fetch license record by key."""
        resp = requests.get(
            f"{self.url}/rest/v1/licenses",
            params={"key": f"eq.{license_key}", "select": "*"},
            headers=self._headers,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return {"valid": False, "error": "License key not found."}
        return data[0]
