#!/usr/bin/env pwsh
# Start MSR Event Hub: Build frontend and launch server
# Compatible with Windows PowerShell

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "MSR Event Hub Startup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\.venv\Scripts\Activate.ps1

# Check if dependencies are installed
$pythonPackages = & .\.venv\Scripts\pip.exe list 2>&1
if (-not ($pythonPackages -match "fastapi")) {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    & .\.venv\Scripts\pip.exe install fastapi uvicorn[standard] azure-identity python-dotenv pydantic pydantic-settings agent-framework-azure-ai
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
}
Write-Host ""

# Check if frontend needs building
$frontendDist = Join-Path $PSScriptRoot "web\chat\dist"
$frontendPackageJson = Join-Path $PSScriptRoot "web\chat\package.json"

if (Test-Path $frontendPackageJson) {
    if (-not (Test-Path $frontendDist)) {
        Write-Host "Frontend not built. Building..." -ForegroundColor Yellow
        
        Push-Location (Join-Path $PSScriptRoot "web\chat")
        try {
            # Install dependencies if node_modules missing
            if (-not (Test-Path "node_modules")) {
                Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
                npm install
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "ERROR: npm install failed" -ForegroundColor Red
                    Pop-Location
                    exit 1
                }
            }
            
            # Build frontend
            Write-Host "Building frontend..." -ForegroundColor Yellow
            npm run build
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR: Frontend build failed" -ForegroundColor Red
                Pop-Location
                exit 1
            }
            
            Write-Host "✓ Frontend built successfully" -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Host "✓ Frontend already built" -ForegroundColor Green
    }
} else {
    Write-Host "⚠ Frontend package.json not found, skipping build" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting MSR Event Hub server..." -ForegroundColor Cyan
Write-Host ""

# Check for .env file
$envFile = Join-Path $PSScriptRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "⚠ No .env file found. Copy .env.example to .env and configure:" -ForegroundColor Yellow
    Write-Host "   cp .env.example .env" -ForegroundColor Yellow
    Write-Host ""
}

# Start Python server (using venv Python)
& .\.venv\Scripts\python.exe main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Server failed to start" -ForegroundColor Red
    Write-Host "Check logs above for details" -ForegroundColor Yellow
    exit 1
}
