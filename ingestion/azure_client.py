"""Azure authentication and client helpers for InfraLens."""

from __future__ import annotations

import time
from typing import Optional
import requests

from config import (
    AZURE_CLIENT_ID,
    AZURE_CLIENT_SECRET,
    AZURE_TENANT_ID,
)

_CACHED_TOKEN: Optional[str] = None
_TOKEN_EXPIRES_AT: float = 0.0


def is_azure_configured() -> bool:
    """Check if Azure Tenant ID and Service Principal credentials are configured."""
    return bool(AZURE_TENANT_ID and AZURE_CLIENT_ID and AZURE_CLIENT_SECRET)


def get_azure_access_token() -> Optional[str]:
    """Retrieve an Azure OAuth2 Bearer token using Client Credentials grant."""
    global _CACHED_TOKEN, _TOKEN_EXPIRES_AT

    if not is_azure_configured():
        return None

    # Return cached token if still valid (with 60s safety buffer)
    if _CACHED_TOKEN and time.time() < (_TOKEN_EXPIRES_AT - 60):
        return _CACHED_TOKEN

    token_url = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": AZURE_CLIENT_ID,
        "client_secret": AZURE_CLIENT_SECRET,
        "scope": "https://management.azure.com/.default",
    }

    try:
        response = requests.post(token_url, data=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            _CACHED_TOKEN = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            _TOKEN_EXPIRES_AT = time.time() + expires_in
            return _CACHED_TOKEN
        else:
            print(f"Azure authentication returned HTTP {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Azure authentication request failed: {e}")
        return None


def verify_azure_authentication() -> bool:
    """Verify live authentication with Azure Active Directory."""
    token = get_azure_access_token()
    if token:
        print("[OK] Successfully authenticated with Azure Active Directory via Service Principal.")
        return True
    else:
        print("[-] Azure authentication failed or credentials not provided. Using synthetic fallback telemetry.")
        return False
