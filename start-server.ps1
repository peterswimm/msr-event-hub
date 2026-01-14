#!/usr/bin/env pwsh
# Simple server startup script

Write-Host "Building frontend..." -ForegroundColor Cyan
Push-Location "web/chat"
npm run build
Pop-Location

Write-Host ""
Write-Host "Starting backend server..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe main.py
