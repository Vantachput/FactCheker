#!/usr/bin/env bash
# ==============================================================================
# scripts/healthcheck.sh — Production: Перевірка працездатності бота
# ==============================================================================
# Використання: bash scripts/healthcheck.sh
# Повертає exit code 0 якщо все ОК, 1 — якщо є проблеми.
# Призначений для моніторингу (cron, Zabbix, UptimeRobot external check тощо).
# ==============================================================================
set -euo pipefail

SERVICE="factchecker"
DB_FILE="/opt/factchecker/app/bot_data.db"
LOG_FILE="/opt/factchecker/app/bot_usage.log"
ERRORS=0

pass() { echo "  [PASS] $*"; }
fail() { echo "  [FAIL] $*" >&2; ERRORS=$((ERRORS + 1)); }
info() { echo "  [INFO] $*"; }

echo "========================================"
echo "  FactChecker — Health Check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# 1. systemd-сервіс запущений
echo "1. Checking systemd service..."
STATUS=$(systemctl is-active "${SERVICE}.service" || true)
if [[ "$STATUS" == "active" ]]; then
    pass "Service '${SERVICE}' is active."
else
    fail "Service '${SERVICE}' is NOT active (status: ${STATUS})."
fi

# 2. Python-процес бота існує
echo "2. Checking Python process..."
PID=$(pgrep -f "python.*main.py" || true)
if [[ -n "$PID" ]]; then
    MEMORY=$(ps -p "$PID" -o rss= | awk '{printf "%.1f MB", $1/1024}')
    pass "Bot process running (PID: $PID, RAM: $MEMORY)."
else
    fail "Bot process NOT found."
fi

# 3. База даних доступна
echo "3. Checking database..."
if [[ -f "$DB_FILE" ]]; then
    DB_SIZE=$(du -sh "$DB_FILE" | cut -f1)
    INTEGRITY=$(sqlite3 "$DB_FILE" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
    if [[ "$INTEGRITY" == "ok" ]]; then
        pass "Database OK (size: $DB_SIZE, integrity: ok)."
    else
        fail "Database integrity check FAILED: $INTEGRITY"
    fi
else
    fail "Database file not found: $DB_FILE"
fi

# 4. Місце на диску (>10% вільно)
echo "4. Checking disk space..."
DISK_FREE=$(df /opt/factchecker --output=pcent | tail -1 | tr -d '% ')
if [[ "$DISK_FREE" -lt 90 ]]; then
    pass "Disk usage: ${DISK_FREE}% (free: $((100 - DISK_FREE))%)."
else
    fail "Disk usage critically high: ${DISK_FREE}%."
fi

# 5. Логи не містять критичних помилок за останні 5 хвилин
echo "5. Checking recent logs..."
RECENT_ERRORS=$(journalctl -u "${SERVICE}.service" --since "5 minutes ago" -p err --no-pager -q 2>/dev/null | wc -l)
if [[ "$RECENT_ERRORS" -eq 0 ]]; then
    pass "No errors in logs (last 5 min)."
else
    fail "$RECENT_ERRORS error(s) found in logs (last 5 min). Check: journalctl -u ${SERVICE} -p err"
fi

# 6. Вихідний трафік до Telegram API
echo "6. Checking network access (Telegram API)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://api.telegram.org || echo "000")
if [[ "$HTTP_CODE" == "200" || "$HTTP_CODE" == "404" ]]; then
    pass "Telegram API reachable (HTTP $HTTP_CODE)."
else
    fail "Cannot reach api.telegram.org (HTTP $HTTP_CODE). Check firewall/network."
fi

# ---------------------------------------------------------------------------- #
#   Підсумок
# ---------------------------------------------------------------------------- #
echo ""
echo "========================================"
if [[ "$ERRORS" -eq 0 ]]; then
    echo "  [HEALTHY] All checks passed."
    echo "========================================"
    exit 0
else
    echo "  [UNHEALTHY] $ERRORS check(s) failed."
    echo "========================================"
    exit 1
fi
