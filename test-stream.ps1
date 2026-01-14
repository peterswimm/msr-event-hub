#!/usr/bin/env pwsh
# Test the streaming endpoint with Browse All Projects action

$url = "http://localhost:8000/api/chat/stream"
$body = @{
    messages = @(
        @{
            role = "user"
            content = "Browse All Projects"
        }
    )
} | ConvertTo-Json

Write-Host "Testing streaming endpoint..." -ForegroundColor Cyan
Write-Host "URL: $url" -ForegroundColor Yellow
Write-Host ""
Write-Host "Sending request with Browse All Projects action..." -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url `
        -Method POST `
        -Headers @{ "Content-Type" = "application/json" } `
        -Body $body `
        -TimeoutSec 30 `
        -ErrorAction Stop

    Write-Host "Response Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    
    $content = $response.Content
    Write-Host "Response Content (first 2000 chars):" -ForegroundColor Yellow
    Write-Host $content.Substring(0, [Math]::Min(2000, $content.Length)) -ForegroundColor White
    Write-Host ""
    
    # Parse SSE events
    $events = @()
    $lines = $content -split "`n"
    
    foreach ($line in $lines) {
        if ($line.StartsWith("data:")) {
            $json = $line.Substring(5).Trim()
            if ($json -and $json -ne "[DONE]") {
                try {
                    $parsed = $json | ConvertFrom-Json
                    $events += $parsed
                    Write-Host "Event parsed:" -ForegroundColor Green
                    Write-Host "  - Has adaptive_card: $($null -ne $parsed.adaptive_card)" -ForegroundColor Cyan
                    Write-Host "  - Delta length: $($parsed.delta.Length)" -ForegroundColor Cyan
                } catch {
                    Write-Host "Failed to parse: $($json.Substring(0, 100))..." -ForegroundColor Red
                }
            }
        }
    }
    
    Write-Host ""
    Write-Host "Total events received: $($events.Count)" -ForegroundColor Green
    
    $eventWithCard = $events | Where-Object { $null -ne $_.adaptive_card } | Select-Object -First 1
    if ($eventWithCard) {
        Write-Host "✓ Adaptive card found in stream!" -ForegroundColor Green
        Write-Host "Card type: $($eventWithCard.adaptive_card.type)" -ForegroundColor Cyan
    } else {
        Write-Host "✗ No adaptive card found" -ForegroundColor Red
    }
    
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
