#!/usr/bin/env bash
# ==============================================================================
# scripts/deploy.sh — Production: Повне розгортання оновлення
# ==============================================================================
# Виконує: backup → git pull → pip install → restart → healthcheck
#
# Використання: sudo -u factbot bash scripts/deploy.sh
#               (sudo потрібен лише для systemctl restart)
# ==============================================================================
set -euo pipefail

# ---------------------------------------------------------------------------- #
#   Налаштування
# ---------------------------------------------------------------------------- #
APP_DIR="/opt/factchecker/app"
VENV_PY="/opt/factchecker/venv/bin/python"
VENV_PIP="/opt/factchecker/venv/bin/pip"
BACKUP_DIR="/opt/factchecker/backups"
SERVICE="factchecker"
BRANCH="main"
WAIT_AFTER_START=5

# ---------------------------------------------------------------------------- #
#   Допоміжні функції
# ---------------------------------------------------------------------------- #
log()   { echo "[$(date '+%H:%M:%S')] $*"; }
ok()    { echo "[$(date '+%H:%M:%S')] [OK] $*"; }
fail()  { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; exit 1; }

# ---------------------------------------------------------------------------- #
#   Старт
# ---------------------------------------------------------------------------- #
echo "=============================================="
echo "  FactChecker — Deploy Script"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

cd "$APP_DIR" || fail "Директорія $APP_DIR не знайдена"

# 1. Зберегти поточний коміт для можливого відкату
PREV_COMMIT=$(git rev-parse HEAD)
log "Current commit: $PREV_COMMIT"

# 2. Резервне копіювання БД
log "Creating database backup..."
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
sqlite3 "$APP_DIR/bot_data.db" ".backup $BACKUP_DIR/bot_data_$TIMESTAMP.db"
ok "Backup: $BACKUP_DIR/bot_data_$TIMESTAMP.db"

# 3. Отримати нову версію коду
log "Fetching latest code from origin/$BRANCH..."
git fetch origin "$BRANCH"
NEW_COMMIT=$(git rev-parse "origin/$BRANCH")

if [[ "$PREV_COMMIT" == "$NEW_COMMIT" ]]; then
    log "Already up to date. Nothing to deploy."
    exit 0
fi

log "Updating: $PREV_COMMIT → $NEW_COMMIT"
git pull origin "$BRANCH"
ok "Code updated."

# 4. Оновити залежності (тільки якщо requirements.txt змінився)
if git diff "$PREV_COMMIT" HEAD -- requirements.txt | grep -q '^[+-]'; then
    log "requirements.txt changed. Updating dependencies..."
    "$VENV_PIP" install --upgrade pip -q
    "$VENV_PIP" install -r requirements.txt -q
    ok "Dependencies updated."
else
    log "requirements.txt unchanged. Skipping pip install."
fi

# 5. Перезапустити сервіс
log "Restarting service..."
sudo systemctl restart "${SERVICE}.service"
sleep $WAIT_AFTER_START

# 6. Перевірка
STATUS=$(systemctl is-active "${SERVICE}.service" || true)
if [[ "$STATUS" == "active" ]]; then
    ok "Service is running."
else
    fail "Service failed to start (status: $STATUS). Run: sudo journalctl -u ${SERVICE}.service -n 50"
fi

# 7. Зафіксувати успішне оновлення
echo "$(date '+%Y-%m-%d %H:%M:%S') | $PREV_COMMIT → $NEW_COMMIT | OK" \
    >> /opt/factchecker/update_history.log

echo ""
echo "=============================================="
echo "  [DONE] Deploy successful!"
echo "  New commit: $NEW_COMMIT"
echo "  Backup:     $BACKUP_DIR/bot_data_$TIMESTAMP.db"
echo "=============================================="
