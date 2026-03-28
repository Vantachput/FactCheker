#!/usr/bin/env bash
# ==============================================================================
# scripts/rollback.sh — Production: Відкат до попереднього коміту
# ==============================================================================
# Використання: sudo -u factbot bash scripts/rollback.sh [commit-hash]
#
# Якщо commit-hash не вказано — відкат до попереднього коміту (HEAD~1).
# Після відкату коду відновлює БД з найсвіжішого бекапу.
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/factchecker/app"
VENV_PIP="/opt/factchecker/venv/bin/pip"
BACKUP_DIR="/opt/factchecker/backups"
SERVICE="factchecker"

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
ok()   { echo "[$(date '+%H:%M:%S')] [OK] $*"; }
fail() { echo "[$(date '+%H:%M:%S')] [ERROR] $*" >&2; exit 1; }

echo "=============================================="
echo "  FactChecker — Rollback Script"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="

cd "$APP_DIR" || fail "Директорія не знайдена: $APP_DIR"

CURRENT=$(git rev-parse HEAD)
TARGET=${1:-"HEAD~1"}

log "Current commit : $CURRENT"
log "Target commit  : $TARGET"
echo ""
read -rp "Продовжити відкат? [y/N] " CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || { echo "Відкат скасовано."; exit 0; }

# 1. Зупинити сервіс
log "Stopping service..."
sudo systemctl stop "${SERVICE}.service"
ok "Service stopped."

# 2. Відкатити код
log "Rolling back code to: $TARGET"
git checkout "$TARGET"
ok "Code rolled back. Now at: $(git rev-parse HEAD)"

# 3. Відновити залежності попередньої версії
log "Restoring dependencies..."
"$VENV_PIP" install -r requirements.txt -q
ok "Dependencies restored."

# 4. Відновити БД з найсвіжішого бекапу
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/bot_data_*.db 2>/dev/null | head -1 || true)
if [[ -n "$LATEST_BACKUP" ]]; then
    log "Restoring database from: $LATEST_BACKUP"
    cp "$LATEST_BACKUP" "$APP_DIR/bot_data.db"
    ok "Database restored."
else
    log "[WARN] No database backup found. Keeping current database."
fi

# 5. Запустити сервіс
log "Starting service..."
sudo systemctl start "${SERVICE}.service"
sleep 3

STATUS=$(systemctl is-active "${SERVICE}.service" || true)
if [[ "$STATUS" == "active" ]]; then
    ok "Service is running after rollback."
else
    fail "Service failed to start after rollback! Check: journalctl -u ${SERVICE}.service -n 50"
fi

# 6. Зафіксувати відкат
echo "$(date '+%Y-%m-%d %H:%M:%S') | ROLLBACK | $CURRENT → $(git rev-parse HEAD) | DB: $LATEST_BACKUP" \
    >> /opt/factchecker/update_history.log

echo ""
echo "=============================================="
echo "  [DONE] Rollback successful!"
echo "  Rolled back to: $(git rev-parse HEAD)"
echo "=============================================="
