#!/usr/bin/env bash
# ==============================================================================
# scripts/start.sh — Production: Запуск бота через systemd
# ==============================================================================
# Використання: sudo bash scripts/start.sh
# ==============================================================================
set -euo pipefail

SERVICE="factchecker"
LOG_LINES=20

echo "========================================"
echo "  FactChecker — Starting (production)"
echo "========================================"

# Перевірка, чи запускається від root/sudo
if [[ $EUID -ne 0 ]]; then
    echo "[ERROR] Цей скрипт потребує sudo." >&2
    exit 1
fi

# Перевірка, чи сервіс існує
if ! systemctl list-unit-files | grep -q "${SERVICE}.service"; then
    echo "[ERROR] Сервіс '${SERVICE}.service' не знайдено." >&2
    echo "        Спочатку виконайте налаштування згідно docs/deployment.md" >&2
    exit 1
fi

# Запуск
systemctl start "${SERVICE}.service"
echo "[OK] Команда запуску надіслана."

sleep 3

# Перевірка статусу
STATUS=$(systemctl is-active "${SERVICE}.service")
if [[ "$STATUS" == "active" ]]; then
    echo "[OK] Сервіс активний."
else
    echo "[ERROR] Сервіс не запустився. Статус: ${STATUS}" >&2
    echo "--- Останні логи ---"
    journalctl -u "${SERVICE}.service" -n $LOG_LINES --no-pager
    exit 1
fi

echo ""
echo "--- Останні логи ---"
journalctl -u "${SERVICE}.service" -n $LOG_LINES --no-pager
echo ""
echo "[DONE] Бот запущений успішно."
