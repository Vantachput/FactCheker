#!/usr/bin/env bash
# ==============================================================================
# scripts/backup.sh — Production: Резервне копіювання БД та логів
# ==============================================================================
# Використання: bash scripts/backup.sh
# Призначений для запуску через cron (щодня о 03:00):
#   0 3 * * * /bin/bash /opt/factchecker/app/scripts/backup.sh >> /opt/factchecker/backups/backup.log 2>&1
# ==============================================================================
set -euo pipefail

APP_DIR="/opt/factchecker/app"
BACKUP_DIR="/opt/factchecker/backups"
KEEP_DAYS=30     # Кількість днів зберігання бекапів

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Backup started ==="

# 1. SQLite (онлайн-бекап, без зупинки бота)
if [[ -f "$APP_DIR/bot_data.db" ]]; then
    sqlite3 "$APP_DIR/bot_data.db" ".backup $BACKUP_DIR/bot_data_$TIMESTAMP.db"
    SIZE=$(du -sh "$BACKUP_DIR/bot_data_$TIMESTAMP.db" | cut -f1)
    echo "[OK] DB backup: bot_data_$TIMESTAMP.db ($SIZE)"
else
    echo "[WARN] bot_data.db not found, skipping."
fi

# 2. Логи
if [[ -f "$APP_DIR/bot_usage.log" ]]; then
    cp "$APP_DIR/bot_usage.log" "$BACKUP_DIR/bot_usage_$TIMESTAMP.log"
    echo "[OK] Log backup: bot_usage_$TIMESTAMP.log"
fi

if [[ -f "$APP_DIR/usage_analytics.jsonl" ]]; then
    cp "$APP_DIR/usage_analytics.jsonl" "$BACKUP_DIR/usage_analytics_$TIMESTAMP.jsonl"
    echo "[OK] Analytics backup: usage_analytics_$TIMESTAMP.jsonl"
fi

# 3. Очистити старі бекапи (старші за KEEP_DAYS днів)
DELETED=$(find "$BACKUP_DIR" -name "bot_data_*.db" -mtime +$KEEP_DAYS -print -delete | wc -l)
echo "[INFO] Deleted $DELETED old backup(s) older than ${KEEP_DAYS} days."

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === Backup completed ==="
echo ""
