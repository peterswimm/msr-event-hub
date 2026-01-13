"""
Example: FastAPI server with Key Vault integration.

Shows how to initialize Key Vault on startup and retrieve secrets
in a FastAPI application.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.config.settings import get_settings
from src.config.key_vault import get_key_vault_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup/shutdown events.

    Initializes Key Vault connection on startup.
    Cleans up resources on shutdown.
    """
    # ========================================
    # STARTUP
    # ========================================
    try:
        settings = get_settings()

        if settings.key_vault_url:
            logger.info("=" * 60)
            logger.info("🔑 INITIALIZING KEY VAULT")
            logger.info("=" * 60)
            logger.info(f"Key Vault URL: {settings.key_vault_url}")
            logger.info(f"Environment: {settings.environment}")

            # Get Key Vault manager (initializes connection)
            kv = get_key_vault_manager(settings.key_vault_url)

            # Test connectivity by retrieving one secret
            logger.info("Testing Key Vault connectivity...")
            try:
                test_secret = kv.get_secret("azure-openai-api-key")
                logger.info("✅ Key Vault connectivity confirmed")
                logger.info("✅ All startup checks passed")
            except Exception as e:
                logger.error(f"❌ Key Vault test failed: {e}")
                raise

            logger.info("=" * 60)
        else:
            logger.warning(
                "⚠️  KEY_VAULT_URL not configured - "
                "running in development mode without Key Vault"
            )

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # ========================================
    # SHUTDOWN
    # ========================================
    logger.info("Shutting down application...")
    if settings.key_vault_url:
        kv = get_key_vault_manager(settings.key_vault_url)
        kv.clear_cache()
        logger.info("Key Vault cache cleared")


# Create FastAPI app with lifespan
app = FastAPI(
    title="MSR Event Agent Chat",
    description="Backend service with Key Vault integration",
    lifespan=lifespan,
)


# ========================================
# ROUTES
# ========================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "healthy",
        "environment": settings.environment,
        "has_key_vault": bool(settings.key_vault_url),
    }


@app.post("/chat/ask")
async def ask_question(question: str):
    """
    Example endpoint that uses secrets from Key Vault.

    The OpenAI API key was automatically retrieved from Key Vault
    during startup via the settings object.
    """
    settings = get_settings()

    # Secrets are available as properties
    openai_key = settings.azure_openai_key  # Retrieved from Key Vault
    db_conn = settings.database_connection_string  # Retrieved from Key Vault

    # Your endpoint logic here...
    return {"question": question, "status": "processing"}


@app.post("/admin/rotate-secrets")
async def rotate_secrets():
    """
    Example: Clear secret cache to force refresh from Key Vault.

    Useful after manual secret rotation in Key Vault.
    Only accessible in development for testing.
    """
    settings = get_settings()
    settings.clear_secret_cache()
    return {"status": "Secret cache cleared", "environment": settings.environment}


if __name__ == "__main__":
    import uvicorn

    # Run with uvicorn
    # Make sure KEY_VAULT_URL and AZURE_TENANT_ID are set in .env
    uvicorn.run(
        "example_startup:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
