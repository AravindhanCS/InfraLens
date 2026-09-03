"""Unit tests for Azure client and authentication helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from ingestion.azure_client import (
    get_azure_access_token,
    is_azure_configured,
    verify_azure_authentication,
)


def test_is_azure_configured():
    """Verify is_azure_configured returns boolean depending on env."""
    res = is_azure_configured()
    assert isinstance(res, bool)


def test_get_azure_access_token_mock():
    """Test OAuth2 token retrieval with mocked HTTP response."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "access_token": "mocked_azure_jwt_token",
        "expires_in": 3600,
    }

    with patch("requests.post", return_value=fake_response):
        with patch("ingestion.azure_client.AZURE_TENANT_ID", "mock-tenant"):
            with patch("ingestion.azure_client.AZURE_CLIENT_ID", "mock-client"):
                with patch("ingestion.azure_client.AZURE_CLIENT_SECRET", "mock-secret"):
                    token = get_azure_access_token()
                    assert token == "mocked_azure_jwt_token"


def test_verify_azure_authentication_success():
    """Test verify_azure_authentication when token is available."""
    with patch("ingestion.azure_client.get_azure_access_token", return_value="valid-token"):
        assert verify_azure_authentication() is True


def test_verify_azure_authentication_failure():
    """Test verify_azure_authentication fallback when token fails."""
    with patch("ingestion.azure_client.get_azure_access_token", return_value=None):
        assert verify_azure_authentication() is False
