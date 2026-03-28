#!/usr/bin/env bash
# ==============================================================================
# scripts/stop.sh — Production: Зупинка бота
# ==============================================================================
# Використання: sudo bash scripts/stop.sh
# ==============================================================================
set -euo pipefail

SERVICE="factchecker"

echo "========================================"
echo "  FactChecker — Stopping (production)"
echo "========================================"

if [[ $EUID -ne 0 ]]; then
    echo "[ERROR] Цей скрипт потребує sudo." >&2
    exit 1
fi

STATUS=$(systemctl is-active "${SERVICE}.service" || true)
if [[ "$STATUS" != "active" ]]; then
    echo "[WARN] Сервіс вже не запущений (статус: ${STATUS})."
    exit 0
fi

systemctl stop "${SERVICE}.service"
echo "[OK] Сервіс зупинений."

# Підтвердження
NEW_STATUS=$(systemctl is-active "${SERVICE}.service" || true)
echo "[INFO] Поточний статус: ${NEW_STATUS}"
