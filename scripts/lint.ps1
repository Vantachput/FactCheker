# ==============================================================================
# scripts/lint.ps1 — Windows Dev: Перевірка та форматування коду
# ==============================================================================
# Використання (PowerShell):
#   .\scripts\lint.ps1 [-Fix] [-FormatOnly]
# ==============================================================================

param (
    [switch]$Fix,
    [switch]$FormatOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPy      = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FactChecker — Code Style (Ruff)"       -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $VenvPy)) {
    Write-Host "[ERROR] Virtual environment not found. Run python -m venv .venv first." -ForegroundColor Red
    exit 1
}

Set-Location $ProjectRoot

if ($FormatOnly) {
    Write-Host "[INFO] Formatting code..." -ForegroundColor Gray
    & $VenvPy -m ruff format .
} elseif ($Fix) {
    Write-Host "[INFO] Auto-fixing lint issues..." -ForegroundColor Gray
    & $VenvPy -m ruff check --fix .
    Write-Host "[INFO] Formatting code..." -ForegroundColor Gray
    & $VenvPy -m ruff format .
} else {
    Write-Host "[INFO] Linting code (read-only)..." -ForegroundColor Gray
    & $VenvPy -m ruff check .
}
