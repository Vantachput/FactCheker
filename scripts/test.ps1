# ==============================================================================
# scripts/test.ps1 — Windows Dev: Запуск тестів
# ==============================================================================
# Використання (PowerShell):
#   .\scripts\test.ps1 [-Coverage]
# ==============================================================================

param (
    [switch]$Coverage
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPy      = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FactChecker — Running Tests"          -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $VenvPy)) {
    Write-Host "[ERROR] Virtual environment not found. Run python -m venv .venv first." -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot

if ($Coverage) {
    Write-Host "[INFO] Running pytest with coverage..." -ForegroundColor Gray
    & $VenvPy -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html
} else {
    Write-Host "[INFO] Running pytest..." -ForegroundColor Gray
    & $VenvPy -m pytest tests/ -v --tb=short
}
