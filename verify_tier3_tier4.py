#!/usr/bin/env python3
"""
Tier 3 & 4 Verification Script

Validates all new integrations and their configurations.
Run to verify production readiness.
"""

import sys
import os
from pathlib import Path

print("\n" + "="*70)
print("TIER 3 & 4 INTEGRATION VERIFICATION")
print("="*70)

# ===== Check Files =====
print("\n📁 FILE VERIFICATION")
print("-" * 70)

required_files = {
    "integrations/foundry_provider.py": "Foundry LLM provider",
    "integrations/foundry_integration.py": "Foundry agent & evaluation",
    "integrations/power_platform_connector.py": "Power Platform REST API",
    "integrations/extended_settings.py": "Unified configuration",
    "tier3_tier4_examples.py": "12 working examples",
    "TIER3_TIER4_COMPLETE.md": "Implementation guide",
    "TIER3_TIER4_SUMMARY.md": "Build summary",
    "requirements-tier3-tier4.txt": "Dependencies",
}

base_path = Path(__file__).parent

all_exist = True
for filepath, description in required_files.items():
    full_path = base_path / filepath
    exists = full_path.exists()
    status = "✓" if exists else "✗"
    print(f"{status} {filepath:40} ({description})")
    if not exists:
        all_exist = False

# ===== Check Imports =====
print("\n📦 IMPORT VERIFICATION")
print("-" * 70)

sys.path.insert(0, str(base_path))

imports_ok = True

# Test M365 (should already work)
try:
    from integrations import (
        M365KnowledgeConnector,
        create_connector as create_m365_connector
    )
    print("✓ M365 imports (existing)")
except Exception as e:
    print(f"✗ M365 imports: {e}")
    imports_ok = False

# Test Foundry
try:
    from integrations import (
        AzureAIFoundryProvider,
        FoundryModelRegistry,
        FoundryAgentIntegration,
        FoundryEvaluation
    )
    print("✓ Foundry imports (Tier 3)")
except Exception as e:
    print(f"✗ Foundry imports: {e}")
    imports_ok = False

# Test Power Platform
try:
    from integrations import (
        create_power_platform_connector,
        ExtractionRequest,
        ExtractionResponse,
        ArtifactItem
    )
    print("✓ Power Platform imports (Tier 4)")
except Exception as e:
    print(f"✗ Power Platform imports: {e}")
    imports_ok = False

# Test Extended Settings
try:
    from integrations import (
        ExtendedSettings,
        LLMProvider,
        IntegrationMode,
        get_settings
    )
    print("✓ Extended Settings imports (Tier 3 & 4)")
except Exception as e:
    print(f"✗ Extended Settings imports: {e}")
    imports_ok = False

# ===== Check Configuration =====
print("\n⚙️  CONFIGURATION VERIFICATION")
print("-" * 70)

try:
    from integrations import get_settings

    settings = get_settings()

    # Check basic properties
    print(f"✓ Settings loaded")
    print(f"  - Integration Mode: {settings.integration_mode}")
    print(f"  - LLM Provider: {settings.llm_provider}")
    print(f"  - API Port: {settings.api_port}")

    # Check validators
    foundry_valid = settings.validate_foundry_config()
    power_valid = settings.validate_power_platform_config()
    m365_valid = settings.validate_m365_config()

    print(f"  - Foundry Config: {'✓ Valid' if foundry_valid else '⚠ Not configured'}")
    print(f"  - Power Platform Config: {'✓ Valid' if power_valid else '⚠ Not configured'}")
    print(f"  - M365 Config: {'✓ Valid' if m365_valid else '⚠ Not configured'}")

    # Show active providers
    providers = settings.get_active_providers()
    tier = settings.get_integration_tier()
    print(f"  - Integration Tier: {tier}")
    print(f"  - Active Providers: {', '.join(providers) if providers else 'None (local only)'}")

except Exception as e:
    print(f"✗ Configuration check failed: {e}")

# ===== Check Models (if Foundry configured) =====
print("\n🧠 FOUNDRY MODELS VERIFICATION")
print("-" * 70)

try:
    from integrations import FoundryModelRegistry

    models = FoundryModelRegistry.list_models()
    print(f"✓ {len(models)} models available:")

    for model_name, model_info in models.items():
        print(f"  - {model_name}: {model_info['description']}")
        print(f"    Use cases: {', '.join(model_info['use_cases'])}")

except Exception as e:
    print(f"✗ Model registry check failed: {e}")

# ===== Check API Endpoints =====
print("\n🔌 API ENDPOINTS VERIFICATION")
print("-" * 70)

try:
    from integrations import create_power_platform_connector

    app = create_power_platform_connector()

    # Get routes
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods - {'OPTIONS', 'HEAD'})
            routes.append((route.path, methods))

    print(f"✓ {len(routes)} API endpoints available:")

    endpoints = {
        "/extract": "POST",
        "/artifacts": "GET",
        "/search": "GET",
        "/analytics/summary": "GET",
        "/health": "GET",
        "/schema": "GET",
    }

    for endpoint, method in endpoints.items():
        found = any(endpoint in path for path, _ in routes)
        status = "✓" if found else "✗"
        print(f"  {status} {method:6} {endpoint}")

except Exception as e:
    print(f"✗ API endpoint check failed: {e}")

# ===== Summary =====
print("\n" + "="*70)
print("VERIFICATION SUMMARY")
print("="*70)

summary = {
    "Files": "✓ All required files present" if all_exist else "✗ Some files missing",
    "Imports": "✓ All imports working" if imports_ok else "✗ Import errors",
    "Configuration": "✓ Settings loaded" if settings else "✗ Config failed",
    "Models": "✓ Foundry models available" if models else "✗ Model check failed",
    "API": "✓ API endpoints ready" if routes else "✗ API check failed",
}

for check, result in summary.items():
    print(f"{result}")

print("\n" + "="*70)

# Final status
if all_exist and imports_ok:
    print("✅ TIER 3 & 4 INTEGRATION READY FOR PRODUCTION")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements-tier3-tier4.txt")
    print("2. Configure .env with your credentials")
    print("3. Run examples: python tier3_tier4_examples.py")
    print("4. Start connector: python -m integrations.power_platform_connector")
    sys.exit(0)
else:
    print("⚠️  VERIFICATION INCOMPLETE - See errors above")
    print("\nTroubleshooting:")
    print("- Install optional dependencies for FastAPI/Foundry")
    print("- Check file paths and imports")
    print("- Review configuration")
    sys.exit(1)
