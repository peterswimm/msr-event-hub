"""
Unit tests for Azure Key Vault integration.

Covers KeyVaultManager initialization, secret retrieval, caching behavior,
singleton usage, and error handling. Uses mocks to avoid real network calls.
"""

import pytest
from unittest.mock import patch, MagicMock
from azure.core.exceptions import ResourceNotFoundError, AuthenticationError

from config.key_vault import KeyVaultManager, get_key_vault_manager


# ==========================
# Fixtures
# ==========================


@pytest.fixture
def valid_vault_url():
    return "https://kv-test.vault.azure.net/"


@pytest.fixture
def invalid_vault_urls():
    return [
        "http://kv-test.vault.azure.net/",  # wrong scheme
        "kv-test.vault.azure.net/",          # missing scheme
        "",                                  # empty
        None,                                 # None
    ]


@pytest.fixture
def mock_secret_client():
    client = MagicMock()
    secret = MagicMock()
    secret.value = "secret-value"
    client.get_secret.return_value = secret
    return client


# ==========================
# Initialization
# ==========================


class TestInitialization:
    def test_init_with_valid_url_managed_identity(self, valid_vault_url):
        with patch("config.key_vault.ManagedIdentityCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                manager = KeyVaultManager(valid_vault_url, use_managed_identity=True)
                assert manager.vault_url == valid_vault_url
                mock_client_class.assert_called_once()

    def test_init_with_valid_url_default_credential(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                manager = KeyVaultManager(valid_vault_url, use_managed_identity=False)
                assert manager.vault_url == valid_vault_url
                mock_client_class.assert_called_once()

    def test_init_with_invalid_url_raises(self, invalid_vault_urls):
        for bad_url in invalid_vault_urls:
            with pytest.raises(ValueError, match="Invalid vault URL"):
                KeyVaultManager(bad_url)

    def test_init_fallback_to_default_credential(self, valid_vault_url):
        with patch("config.key_vault.ManagedIdentityCredential", side_effect=Exception("not available")):
            with patch("config.key_vault.DefaultAzureCredential"):
                with patch("config.key_vault.SecretClient"):
                    manager = KeyVaultManager(valid_vault_url, use_managed_identity=True)
                    assert manager.vault_url == valid_vault_url

    def test_init_authentication_error(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient", side_effect=AuthenticationError("Auth failed")):
                with pytest.raises(AuthenticationError):
                    KeyVaultManager(valid_vault_url)


# ==========================
# Secret retrieval and caching
# ==========================


class TestSecretRetrieval:
    def test_get_secret_success(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                secret = MagicMock()
                secret.value = "test-secret-value"
                mock_client.get_secret.return_value = secret

                manager = KeyVaultManager(valid_vault_url)
                result = manager.get_secret("test-key")

                assert result == "test-secret-value"
                mock_client.get_secret.assert_called_once_with("test-key")

    def test_get_secret_not_found(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_secret.side_effect = ResourceNotFoundError("Secret not found")

                manager = KeyVaultManager(valid_vault_url)

                with pytest.raises(ValueError, match="not found in Key Vault"):
                    manager.get_secret("missing-key")

    def test_get_secret_with_caching(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                secret = MagicMock()
                secret.value = "cached-value"
                mock_client.get_secret.return_value = secret

                manager = KeyVaultManager(valid_vault_url)

                result1 = manager.get_secret("cache-key", use_cache=True)
                result2 = manager.get_secret("cache-key", use_cache=True)

                assert result1 == result2 == "cached-value"
                assert mock_client.get_secret.call_count == 1  # second call cached

    def test_sensitive_keys_not_cached(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                secret = MagicMock()
                secret.value = "sensitive"
                mock_client.get_secret.return_value = secret

                manager = KeyVaultManager(valid_vault_url)

                manager.get_secret("encryption-master-key", use_cache=True)
                manager.get_secret("encryption-master-key", use_cache=True)

                assert mock_client.get_secret.call_count == 2  # not cached

    def test_get_secret_without_cache(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                secret = MagicMock()
                secret.value = "no-cache"
                mock_client.get_secret.return_value = secret

                manager = KeyVaultManager(valid_vault_url)
                manager.get_secret("plain-key", use_cache=False)
                manager.get_secret("plain-key", use_cache=False)

                assert mock_client.get_secret.call_count == 2


# ==========================
# Cache management
# ==========================


class TestCacheManagement:
    def test_clear_cache(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                secret = MagicMock()
                secret.value = "val"
                mock_client.get_secret.return_value = secret

                manager = KeyVaultManager(valid_vault_url)
                manager.get_secret("key1", use_cache=True)
                assert len(manager._cache) == 1

                manager.clear_cache()
                assert len(manager._cache) == 0

    def test_cache_persistence_multiple_keys(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                secret = MagicMock()
                secret.value = "val"
                mock_client.get_secret.return_value = secret

                manager = KeyVaultManager(valid_vault_url)
                manager.get_secret("k1", use_cache=True)
                manager.get_secret("k2", use_cache=True)
                manager.get_secret("k3", use_cache=True)

                assert set(manager._cache.keys()) == {"k1", "k2", "k3"}


# ==========================
# Singleton behavior
# ==========================


class TestSingleton:
    def test_singleton_same_instance(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient"):
                get_key_vault_manager.cache_clear()
                m1 = get_key_vault_manager(valid_vault_url)
                m2 = get_key_vault_manager(valid_vault_url)
                assert m1 is m2

    def test_singleton_different_vaults(self):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient"):
                get_key_vault_manager.cache_clear()
                v1 = "https://kv-1.vault.azure.net/"
                v2 = "https://kv-2.vault.azure.net/"
                m1 = get_key_vault_manager(v1)
                m2 = get_key_vault_manager(v2)
                assert m1 is not m2


# ==========================
# Error handling
# ==========================


class TestErrorHandling:
    def test_exception_during_secret_retrieval(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_secret.side_effect = Exception("Network error")

                manager = KeyVaultManager(valid_vault_url)
                with pytest.raises(Exception, match="Network error"):
                    manager.get_secret("any")

    def test_invalid_secret_name(self, valid_vault_url):
        with patch("config.key_vault.DefaultAzureCredential"):
            with patch("config.key_vault.SecretClient") as mock_client_class:
                mock_client = MagicMock()
                mock_client_class.return_value = mock_client
                mock_client.get_secret.side_effect = ResourceNotFoundError("bad")

                manager = KeyVaultManager(valid_vault_url)
                with pytest.raises(ValueError):
                    manager.get_secret("")