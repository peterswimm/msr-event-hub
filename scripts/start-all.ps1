#!/usr/bin/env pwsh
# Unified Startup Script for MSR Event Hub + Bridge
# Starts both the bridge (Node.js) and chat backend (Python) in parallel

param(
    [switch]$Frontend,  # Also start frontend dev server
    [switch]$NoBridge   # Skip starting the bridge
)

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "MSR Event Hub - Unified Startup" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Get paths (script is in scripts/ subdirectory, so go up to project root first)
$chatPath = Split-Path $PSScriptRoot -Parent
$bridgePath = Join-Path (Split-Path $chatPath -Parent) "msr-event-agent-bridge"

# Validate paths
if (-not (Test-Path $chatPath)) {
    Write-Host "ERROR: Chat path not found: $chatPath" -ForegroundColor Red
    exit 1
}

if (-not $NoBridge -and -not (Test-Path $bridgePath)) {
    Write-Host "ERROR: Bridge path not found: $bridgePath" -ForegroundColor Red
    Write-Host "Expected: $bridgePath" -ForegroundColor Yellow
    Write-Host "Use -NoBridge flag to skip bridge startup" -ForegroundColor Yellow
    exit 1
}

# Check for running processes on ports
$ports = @(3000, 8000, 5173)
Write-Host "Checking for processes on ports: $($ports -join ', ')..." -ForegroundColor Cyan

foreach ($port in $ports) {
    $connections = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    if ($connections) {
        Write-Host "⚠️  Port $port is already in use" -ForegroundColor Yellow
        $processId = ($connections -split '\s+')[-1]
        $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($process) {
            Write-Host "   Process: $($process.ProcessName) (PID: $processId)" -ForegroundColor Gray
        }
    }
}
Write-Host ""

# Function to start process in new window
function Start-ServiceWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command,
        [string]$Icon = "⚙️"
    )
    
    Write-Host "$Icon Starting $Title..." -ForegroundColor Cyan
    
    $encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes(@"
Write-Host '======================================' -ForegroundColor Cyan
Write-Host '$Title' -ForegroundColor Cyan
Write-Host '======================================' -ForegroundColor Cyan
Write-Host ''
Set-Location '$WorkingDirectory'
$Command
"@))
    
    Start-Process pwsh -ArgumentList "-NoExit", "-EncodedCommand", $encodedCommand
    Start-Sleep -Milliseconds 500
}

# Start Bridge (if not skipped)
if (-not $NoBridge) {
    $bridgePackageJson = Join-Path $bridgePath "package.json"
    if (Test-Path $bridgePackageJson) {
        # Check if node_modules exists
        $bridgeNodeModules = Join-Path $bridgePath "node_modules"
        if (-not (Test-Path $bridgeNodeModules)) {
            Write-Host "📦 Installing bridge dependencies..." -ForegroundColor Yellow
            Push-Location $bridgePath
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR: Failed to install bridge dependencies" -ForegroundColor Red
                Pop-Location
                exit 1
            }
            Pop-Location
            Write-Host "✓ Bridge dependencies installed" -ForegroundColor Green
        }
        
        Start-ServiceWindow -Title "Event Hub Bridge (Port 3000)" `
                           -WorkingDirectory $bridgePath `
                           -Command "npm run dev" `
                           -Icon "🌉"
        Write-Host "✓ Bridge starting on port 3000" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Bridge package.json not found, skipping" -ForegroundColor Yellow
    }
} else {
    Write-Host "⏭️  Bridge startup skipped (-NoBridge flag)" -ForegroundColor Gray
}

Write-Host ""

# Start Chat Backend
Write-Host "🐍 Starting Chat Backend (Port 8000)..." -ForegroundColor Cyan

# Check if virtual environment exists
$venvPath = Join-Path $chatPath ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    Push-Location $chatPath
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Pop-Location
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

Start-ServiceWindow -Title "Event Hub Chat Backend (Port 8000)" `
                   -WorkingDirectory $chatPath `
                   -Command ".\scripts\start.ps1" `
                   -Icon "🐍"
Write-Host "✓ Chat backend starting on port 8000" -ForegroundColor Green

Write-Host ""

# Start Frontend Dev Server (optional)
if ($Frontend) {
    $frontendPath = Join-Path $chatPath "web\chat"
    $frontendPackageJson = Join-Path $frontendPath "package.json"
    
    if (Test-Path $frontendPackageJson) {
        # Check if node_modules exists
        $frontendNodeModules = Join-Path $frontendPath "node_modules"
        if (-not (Test-Path $frontendNodeModules)) {
            Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
            Push-Location $frontendPath
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Host "ERROR: Failed to install frontend dependencies" -ForegroundColor Red
                Pop-Location
                exit 1
            }
            Pop-Location
            Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
        }
        
        Write-Host "⚛️  Starting Frontend Dev Server (Port 5173)..." -ForegroundColor Cyan
        Start-ServiceWindow -Title "Event Hub Frontend (Port 5173)" `
                           -WorkingDirectory $frontendPath `
                           -Command "npm run dev" `
                           -Icon "⚛️"
        Write-Host "✓ Frontend starting on port 5173" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Frontend package.json not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "⏭️  Frontend dev server not started (use -Frontend flag to include)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "✓ All services starting!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services:" -ForegroundColor Cyan
if (-not $NoBridge) {
    Write-Host "  🌉 Bridge:   http://localhost:3000" -ForegroundColor White
}
Write-Host "  🐍 Backend:  http://localhost:8000/api" -ForegroundColor White
if ($Frontend) {
    Write-Host "  ⚛️  Frontend: http://localhost:5173" -ForegroundColor White
}
Write-Host ""
Write-Host "To stop all services: Close the terminal windows or use Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "Usage examples:" -ForegroundColor Gray
Write-Host "  ./start-all.ps1              # Bridge + Backend only" -ForegroundColor Gray
Write-Host "  ./start-all.ps1 -Frontend    # Bridge + Backend + Frontend" -ForegroundColor Gray
Write-Host "  ./start-all.ps1 -NoBridge    # Backend only" -ForegroundColor Gray
Write-Host ""
