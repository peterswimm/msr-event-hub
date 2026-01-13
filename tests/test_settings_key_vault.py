"""
Tests for Settings class with Key Vault integration.

Ensures secret properties fetch from Key Vault via the manager and that
caching and cache clearing behave as expected.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.config.settings import Settings


def test_settings_load_from_env(monkeypatch):
    """Verify base fields load from environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("KEY_VAULT_URL", "https://kv-test.vault.azure.net/")
    monkeypatch.setenv("AZURE_TENANT_ID", "tenant-123")

    settings = Settings()
    assert settings.environment == "production"
    assert settings.key_vault_url == "https://kv-test.vault.azure.net/"
    assert settings.azure_tenant_id == "tenant-123"


def test_azure_openai_key_from_vault(monkeypatch):
    """azure_openai_key property pulls from Key Vault via manager."""
    monkeypatch.setenv("KEY_VAULT_URL", "https://kv-test.vault.azure.net/")

    with patch("config.key_vault.get_key_vault_manager") as mock_get:
        mock_mgr = MagicMock()
        mock_mgr.get_secret.return_value = "api-key"
        mock_get.return_value = mock_mgr

        settings = Settings()
        api_key = settings.azure_openai_key

        assert api_key == "api-key"
        mock_mgr.get_secret.assert_called_with("azure-openai-api-key")


def test_database_connection_string_from_vault(monkeypatch):
    """database_connection_string property pulls from Key Vault."""
    monkeypatch.setenv("KEY_VAULT_URL", "https://kv-test.vault.azure.net/")

    with patch("config.key_vault.get_key_vault_manager") as mock_get:
        mock_mgr = MagicMock()
        mock_mgr.get_secret.return_value = "postgresql://u:p@h/db"
        mock_get.return_value = mock_mgr

        settings = Settings()
        conn = settings.database_connection_string

        assert conn == "postgresql://u:p@h/db"
        mock_mgr.get_secret.assert_called_with("database-connection-string")


def test_encryption_master_key_not_cached(monkeypatch):
    """encryption_master_key should not be cached between calls."""
    monkeypatch.setenv("KEY_VAULT_URL", "https://kv-test.vault.azure.net/")

    with patch("config.key_vault.get_key_vault_manager") as mock_get:
        mock_mgr = MagicMock()
        mock_mgr.get_secret.return_value = "master-key"
        mock_get.return_value = mock_mgr

        settings = Settings()

        k1 = settings.encryption_master_key
        k2 = settings.encryption_master_key

        assert k1 == k2 == "master-key"
        # Called twice because not cached
        assert mock_mgr.get_secret.call_count == 2


def test_clear_secret_cache(monkeypatch):
    """clear_secret_cache clears local cache and manager cache."""
    monkeypatch.setenv("KEY_VAULT_URL", "https://kv-test.vault.azure.net/")

    with patch("config.key_vault.get_key_vault_manager") as mock_get:
        mock_mgr = MagicMock()
        mock_mgr.get_secret.return_value = "api-key"
        mock_get.return_value = mock_mgr

        settings = Settings()
        # populate cache
        _ = settings.azure_openai_key
        assert settings._azure_openai_key == "api-key"

        settings.clear_secret_cache()

        assert settings._azure_openai_key is None
        assert settings._database_connection_string is None
        assert settings._redis_password is None
        mock_mgr.clear_cache.assert_called_once()