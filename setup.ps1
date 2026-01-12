# Installation and Setup Script for Modernized Knowledge Agent
# Run this script to set up your environment

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Knowledge Agent Modernization Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

if ($pythonVersion -notmatch "Python 3\.(10|11|12)") {
    Write-Host "WARNING: Python 3.10+ required. Please upgrade Python." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "`nInstalling dependencies (with --pre flag for preview packages)..." -ForegroundColor Yellow
pip install --pre -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green

# Check for .env file
Write-Host "`nChecking environment configuration..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "`nIMPORTANT: Update .env with your credentials:" -ForegroundColor Yellow
    Write-Host "  - FOUNDRY_PROJECT_ENDPOINT" -ForegroundColor Cyan
    Write-Host "  - FOUNDRY_MODEL_DEPLOYMENT" -ForegroundColor Cyan
    Write-Host "  - AZURE_OPENAI_ENDPOINT (optional)" -ForegroundColor Cyan
    Write-Host "  - AZURE_OPENAI_KEY (optional)" -ForegroundColor Cyan
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update .env with your credentials" -ForegroundColor White
Write-Host "2. Enable tracing: AI Toolkit -> 'Start Trace Collector'" -ForegroundColor White
Write-Host "3. Run examples: python examples_modern.py" -ForegroundColor White
Write-Host "4. View traces: AI Toolkit -> 'View Trace'" -ForegroundColor White

Write-Host "`nDocumentation:" -ForegroundColor Yellow
Write-Host "- Quick Start: QUICKSTART.md" -ForegroundColor White
Write-Host "- Full Guide: MODERNIZATION_GUIDE.md" -ForegroundColor White
Write-Host "- Summary: MODERNIZATION_SUMMARY.md" -ForegroundColor White

Write-Host "`nHappy building! 🚀`n" -ForegroundColor Green
