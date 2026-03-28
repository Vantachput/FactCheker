# ==============================================================================
# scripts/dev.ps1 — Windows Dev: Запуск бота у режимі розробки
# ==============================================================================
# Використання (PowerShell):
#   .\scripts\dev.ps1
#
# Якщо виникає помилка виконання політики:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
# ==============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPy      = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$EnvFile     = Join-Path $ProjectRoot ".env"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FactChecker — Dev Mode (Windows)"     -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Перевірка Python у venv
if (-not (Test-Path $VenvPy)) {
    Write-Host "[ERROR] Virtual environment not found." -ForegroundColor Red
    Write-Host "        Run: python -m venv .venv" -ForegroundColor Yellow
    Write-Host "        Then: .venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# 2. Перевірка .env
if (-not (Test-Path $EnvFile)) {
    Write-Host "[ERROR] .env file not found." -ForegroundColor Red
    Write-Host "        Run: copy .env.example .env" -ForegroundColor Yellow
    Write-Host "        Then fill in your API keys." -ForegroundColor Yellow
    exit 1
}

# 3. Показати поточний git-коміт
$Commit = git rev-parse --short HEAD 2>$null
if ($Commit) {
    Write-Host "[INFO] Git commit: $Commit" -ForegroundColor Gray
}

Write-Host "[INFO] Python: $VenvPy" -ForegroundColor Gray
Write-Host "[INFO] Starting bot... (Ctrl+C to stop)" -ForegroundColor Gray
Write-Host ""

# 4. Змінити директорію та запустити
Set-Location $ProjectRoot
& $VenvPy main.py
