"""
Azure Key Vault integration for secure secrets management.

Retrieves secrets at runtime from Key Vault instead of storing them
in environment variables or files. Implements caching and automatic
retry logic for reliability.
"""

import logging
from typing import Optional, Dict, Any
from functools import lru_cache
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from azure.core.exceptions import ResourceNotFoundError, AuthenticationError

logger = logging.getLogger(__name__)


class KeyVaultManager:
    """
    Manages secure retrieval of secrets from Azure Key Vault.
    
    Supports both Managed Identity (production) and interactive authentication (dev).
    Implements optional caching for performance, excluding highly sensitive keys.
    """
    
    def __init__(self, vault_url: str, use_managed_identity: bool = True):
        """
        Initialize Key Vault client.
        
        Args:
            vault_url: Azure Key Vault URL (e.g., https://kv-xxx.vault.azure.net/)
            use_managed_identity: Use Managed Identity (production) vs. interactive auth (dev)
        
        Raises:
            ValueError: If vault_url is invalid
            AuthenticationError: If authentication fails
        """
        if not vault_url or not vault_url.startswith("https://"):
            raise ValueError(f"Invalid vault URL: {vault_url}")
        
        self.vault_url = vault_url
        self._cache: Dict[str, Any] = {}
        
        # Initialize credential based on environment
        try:
            if use_managed_identity:
                try:
                    credential = ManagedIdentityCredential()
                    logger.info("Initialized Managed Identity credential for Key Vault")
                except Exception as e:
                    logger.warning(
                        f"Managed Identity unavailable ({e}), "
                        "falling back to DefaultAzureCredential"
                    )
                    credential = DefaultAzureCredential()
            else:
                credential = DefaultAzureCredential()
            
            self.client = SecretClient(vault_url=vault_url, credential=credential)
            logger.info(f"✅ Key Vault client initialized: {vault_url}")
        
        except AuthenticationError as e:
            logger.error(f"❌ Authentication failed for Key Vault: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Key Vault client: {e}")
            raise
    
    def get_secret(self, secret_name: str, use_cache: bool = True) -> str:
        """
        Retrieve secret from Key Vault with optional caching.
        
        Args:
            secret_name: Name of the secret in Key Vault (kebab-case)
            use_cache: Whether to cache the secret for performance
        
        Returns:
            Secret value as string
        
        Raises:
            ResourceNotFoundError: If secret doesn't exist in Key Vault
            Exception: If retrieval fails
        
        Example:
            >>> kv = KeyVaultManager("https://kv-xxx.vault.azure.net/")
            >>> api_key = kv.get_secret("openai-api-key")
        """
        # Check cache first (except for encryption keys)
        if use_cache and secret_name in self._cache:
            logger.debug(f"Using cached secret: {secret_name}")
            return self._cache[secret_name]
        
        try:
            logger.debug(f"Retrieving secret from Key Vault: {secret_name}")
            secret = self.client.get_secret(secret_name)
            
            # Cache non-sensitive keys (but never cache encryption/signing keys)
            non_cacheable_keys = ["encryption-master-key", "jwt-signing-key"]
            if use_cache and secret_name not in non_cacheable_keys:
                self._cache[secret_name] = secret.value
            
            return secret.value
        
        except ResourceNotFoundError:
            logger.error(f"Secret not found in Key Vault: {secret_name}")
            raise ValueError(f"Secret '{secret_name}' not found in Key Vault")
        except Exception as e:
            logger.error(f"Error retrieving secret '{secret_name}': {e}")
            raise
    
    def clear_cache(self) -> None:
        """Clear the secret cache (useful for testing or forced rotation)."""
        self._cache.clear()
        logger.info("Key Vault cache cleared")


@lru_cache(maxsize=1)
def get_key_vault_manager(vault_url: str) -> KeyVaultManager:
    """
    Get cached Key Vault manager instance.
    
    Uses functools.lru_cache to ensure only one instance per vault URL.
    
    Args:
        vault_url: Azure Key Vault URL
    
    Returns:
        Cached KeyVaultManager instance
    
    Example:
        >>> kv = get_key_vault_manager("https://kv-xxx.vault.azure.net/")
        >>> key = kv.get_secret("openai-api-key")
    """
    return KeyVaultManager(vault_url)
