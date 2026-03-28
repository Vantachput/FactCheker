# Update Guide — FactChecker Production Update Procedure

**Аудиторія:** Release Engineer / DevOps  
**Документ:** Процедура оновлення production-середовища  
**Суміжний документ:** [`deployment.md`](./deployment.md)

---

## Зміст

1. [Підготовка до оновлення](#1-підготовка-до-оновлення)
2. [Процес оновлення](#2-процес-оновлення)
3. [Перевірка після оновлення](#3-перевірка-після-оновлення)
4. [Процедура відкату (Rollback)](#4-процедура-відкату-rollback)

---

## 1. Підготовка до оновлення

### 1.1 Збір інформації про поточний стан

Перед будь-яким оновленням зафіксуйте поточний стан системи.

```bash
# Поточний git-коміт у production
sudo -i -u factbot
cd /opt/factchecker/app
git log --oneline -5
```

Запишіть хеш поточного коміту — він знадобиться для відкату:

```
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "Production commit before update: $CURRENT_COMMIT"
# Збережіть цей хеш у безпечному місці або в тікеті
```

Перевірте статус сервісу та споживання ресурсів:

```bash
sudo systemctl status factchecker.service
ps aux | grep python | grep -v grep
df -h /opt/factchecker
du -sh /opt/factchecker/app/bot_data.db
```

### 1.2 Ознайомлення з CHANGELOG / PR

Перед оновленням обов'язково прочитайте:

- **Список змінених файлів** у новому коміті / pull request
- **`requirements.txt`** — чи змінився список залежностей
- **`pyproject.toml`** — чи змінилась версія проєкту або залежності
- **Файли `database/`** — чи є зміни у структурі БД (нові таблиці, колонки)
- **`.env.example`** — чи додані нові обов'язкові змінні середовища

```bash
# Переглянути, що зміниться (порівняти HEAD з origin/main)
exit  # вийти з factbot
cd /opt/factchecker/app
git fetch origin main
git diff HEAD origin/main --stat
git diff HEAD origin/main -- requirements.txt
git diff HEAD origin/main -- .env.example
git diff HEAD origin/main -- database/
```

### 1.3 Перевірка сумісності

| Перевірка | Команда / Дія |
|---|---|
| Версія Python | `python3 --version` → має бути ≥ 3.12 |
| Нові змінні `.env` | `diff .env .env.example` (після `git fetch`) |
| Зміни у БД | переглянути `git diff HEAD origin/main -- database/db_manager.py` |
| Нові залежності | `pip install --dry-run -r requirements.txt` (у venv) |

> **Якщо структура БД змінилась** (нова таблиця або колонка) — ознайомтесь з кроком [2.4 Міграція даних](#24-міграція-даних).

### 1.4 Резервне копіювання

**Обов'язковий крок.** Виконується до будь-яких змін.

#### База даних

```bash
BACKUP_DIR=/opt/factchecker/backups
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# SQLite онлайн-бекап (без зупинки бота)
sqlite3 /opt/factchecker/app/bot_data.db \
    ".backup $BACKUP_DIR/bot_data_$TIMESTAMP.db"

echo "Backup saved: $BACKUP_DIR/bot_data_$TIMESTAMP.db"
ls -lh $BACKUP_DIR/
```

#### Логи (перед ротацією)

```bash
cp /opt/factchecker/app/bot_usage.log \
   $BACKUP_DIR/bot_usage_$TIMESTAMP.log

cp /opt/factchecker/app/usage_analytics.jsonl \
   $BACKUP_DIR/usage_analytics_$TIMESTAMP.jsonl
```

#### Файл конфігурації `.env`

```bash
cp /opt/factchecker/app/.env \
   $BACKUP_DIR/env_$TIMESTAMP.bak
chmod 600 $BACKUP_DIR/env_$TIMESTAMP.bak
```

### 1.5 Планування часу простою

Бот використовує **long-polling** без вебхуків, тому процес оновлення спричиняє **короткочасний простой** (≈15–60 секунд) лише під час рестарту сервісу. У цей проміжок повідомлення від Telegram **не втрачаються** — вони накопичуються і будуть оброблені після перезапуску.

| Сценарій | Час простою | Коли планувати |
|---|---|---|
| Оновлення коду без зміни залежностей | ~15 сек | Будь-який час |
| Оновлення коду + нові залежності | ~30–60 сек | Нічний час |
| Міграція схеми БД | ~30–90 сек | Нічний час, низьке навантаження |

> **Рекомендований час оновлення:** 02:00–05:00 за Kyiv time (мінімальна активність користувачів).

---

## 2. Процес оновлення

### 2.1 Зупинка служби

```bash
# Зупинити бота
sudo systemctl stop factchecker.service

# Переконатись, що процес завершено
sudo systemctl status factchecker.service
# Очікуваний статус: inactive (dead)

# Якщо процес не зупинився протягом 10 сек — примусово:
sudo systemctl kill factchecker.service
```

### 2.2 Розгортання нового коду

```bash
sudo -i -u factbot
cd /opt/factchecker/app

# Переконатись, що немає незбережених локальних змін
git status
# Якщо є — зберегти або скасувати:
# git stash   (зберегти)
# git checkout -- .   (скасувати)

# Завантажити нову версію
git pull origin main

# Переконатись, що отримано правильний коміт
git log --oneline -3
```

### 2.3 Оновлення залежностей

```bash
# Виконується тільки якщо requirements.txt змінився
/opt/factchecker/venv/bin/pip install --upgrade pip
/opt/factchecker/venv/bin/pip install -r requirements.txt

# Перевірити, що всі пакети встановлені коректно
/opt/factchecker/venv/bin/pip check
# Очікуваний вивід: "No broken requirements found."
```

Якщо якийсь пакет конфліктує — зверніться до `pyproject.toml` для з'ясування точних версій.

### 2.4 Міграція даних

> Виконується **лише якщо** `git diff` показав зміни у `database/db_manager.py`.

FactChecker використовує SQLite з автоматичним створенням таблиць через `init_db()`. При додаванні **нових таблиць** міграція відбувається автоматично.

При додаванні **нових колонок** до існуючої таблиці виконайте SQL вручну:

```bash
# Підключитись до БД
sqlite3 /opt/factchecker/app/bot_data.db

-- Приклад: додати нову колонку (якщо потрібно)
-- ALTER TABLE usage ADD COLUMN new_field TEXT DEFAULT '';
-- Перевірити схему
.schema usage
.quit
```

> Детальні інструкції з міграції публікуються разом із PR, що вносить зміни до схеми БД.

### 2.5 Оновлення конфігурацій

Порівняйте поточний `.env` з оновленим `.env.example`:

```bash
diff /opt/factchecker/app/.env /opt/factchecker/app/.env.example
```

Якщо у `.env.example` з'явились нові ключі — додайте їх у `.env`:

```bash
nano /opt/factchecker/app/.env
# Додати нові змінні зі значеннями
```

Переконайтесь, що права збережені:

```bash
chmod 600 /opt/factchecker/app/.env
```

Якщо змінився `systemd` unit-файл (у release notes це буде зазначено):

```bash
exit  # вийти з factbot
sudo cp /opt/factchecker/app/docs/factchecker.service \
        /etc/systemd/system/factchecker.service
sudo systemctl daemon-reload
```

### 2.6 Запуск оновленого сервісу

```bash
sudo systemctl start factchecker.service

# Зачекати 5 секунд та перевірити статус
sleep 5
sudo systemctl status factchecker.service
```

---

## 3. Перевірка після оновлення

### 3.1 Перевірка статусу сервісу

```bash
sudo systemctl status factchecker.service
```

**Очікуваний результат:**
```
Active: active (running) since ...
```

### 3.2 Перевірка логів запуску

```bash
# Логи з моменту останнього старту
sudo journalctl -u factchecker.service --since "5 minutes ago"
```

**Ознаки успішного запуску:**
```
🚀 Бот запущений асинхронно...
```

**Ознаки проблем:**

| Помилка у логах | Причина | Дія |
|---|---|---|
| `KeyError: 'NEW_VAR'` | Не додано нову змінну у `.env` | Додати змінну → `systemctl restart` |
| `ModuleNotFoundError` | Залежності не встановлено | `pip install -r requirements.txt` |
| `sqlite3.OperationalError` | Схема БД не відповідає коду | Виконати міграцію (крок 2.4) |
| `Unauthorized` (Telegram) | `BOT_TOKEN` не задано або невірний | Перевірити `.env` |
| `ConnectionRefusedError` | Мережа / firewall | Перевірити outbound-правила UFW |

### 3.3 Функціональна перевірка (E2E)

1. Відкрийте бота у Telegram.
2. Надішліть `/start` — бот має відповісти привітанням та показати меню.
3. Надішліть тестовий новинний текст.
4. Отримайте вердикт (ПРАВДА / МАНІПУЛЯЦІЯ / ФЕЙК / НЕПІДТВЕРДЖЕНО).
5. Перевірте, що лічильник у БД збільшився:

```bash
sqlite3 /opt/factchecker/app/bot_data.db \
    "SELECT * FROM usage ORDER BY date DESC LIMIT 5;"
```

### 3.4 Фіксація успішного оновлення

Після успішної перевірки зафіксуйте результат:

```bash
# Записати новий production-коміт
sudo -i -u factbot
cd /opt/factchecker/app
echo "Updated to: $(git rev-parse HEAD) on $(date)" \
    >> /opt/factchecker/update_history.log
cat /opt/factchecker/update_history.log
```

---

## 4. Процедура відкату (Rollback)

Виконується якщо після оновлення виявлено критичну несправність.

### 4.1 Негайна зупинка

```bash
sudo systemctl stop factchecker.service
```

### 4.2 Відкат коду

```bash
sudo -i -u factbot
cd /opt/factchecker/app

# Варіант 1: повернутись до попереднього коміту (збережено у кроці 1.1)
git checkout <CURRENT_COMMIT>

# Варіант 2: скасувати останній pull
git reset --hard HEAD@{1}

# Підтвердити відкат
git log --oneline -3
```

### 4.3 Відновлення залежностей (якщо оновлювались)

```bash
/opt/factchecker/venv/bin/pip install -r requirements.txt
```

### 4.4 Відновлення бази даних (якщо була міграція)

```bash
exit  # вийти з factbot

BACKUP_FILE=/opt/factchecker/backups/bot_data_<TIMESTAMP>.db

# Зупинитись і переконатись, що сервіс не запущений
sudo systemctl status factchecker.service | grep "inactive"

# Замінити поточну БД резервною копією
sudo -i -u factbot
cp $BACKUP_FILE /opt/factchecker/app/bot_data.db

echo "Database restored from: $BACKUP_FILE"
sqlite3 /opt/factchecker/app/bot_data.db ".tables"
```

### 4.5 Відновлення конфігурації `.env`

```bash
BACKUP_ENV=/opt/factchecker/backups/env_<TIMESTAMP>.bak
cp $BACKUP_ENV /opt/factchecker/app/.env
chmod 600 /opt/factchecker/app/.env
```

### 4.6 Перезапуск після відкату

```bash
exit  # вийти з factbot
sudo systemctl start factchecker.service
sleep 5
sudo systemctl status factchecker.service
sudo journalctl -u factchecker.service -n 20
```

Виконайте функціональну перевірку з [кроку 3.3](#33-функціональна-перевірка-e2e).

### 4.7 Звіт про невдале оновлення

Після відкату зафіксуйте інцидент:

```bash
echo "[ROLLBACK] $(date) — rolled back to $(git rev-parse HEAD). Reason: <опишіть причину>" \
    >> /opt/factchecker/update_history.log
```

Створіть issue у GitHub-репозиторії із логами та описом помилки.

---

## Додаток — Checklist оновлення

### Перед оновленням
- [ ] Поточний коміт записано (`git rev-parse HEAD`)
- [ ] Прочитано CHANGELOG / diff нового коміту
- [ ] Перевірено зміни у `requirements.txt`, `.env.example`, `database/`
- [ ] Резервна копія `bot_data.db` створена з timestamp
- [ ] Резервна копія `.env` створена з timestamp
- [ ] Час оновлення погоджено (нічний час при зміні БД)

### Під час оновлення
- [ ] `systemctl stop factchecker.service` → статус `inactive`
- [ ] `git pull origin main` виконано успішно
- [ ] `pip install -r requirements.txt` виконано (якщо потрібно)
- [ ] Міграція БД виконана (якщо потрібно)
- [ ] Нові змінні додано у `.env` (якщо потрібно)
- [ ] `systemctl start factchecker.service` → статус `active (running)`

### Після оновлення
- [ ] Логи не містять помилок (`journalctl -n 30`)
- [ ] Рядок `🚀 Бот запущений...` присутній у логах
- [ ] E2E-тест пройдено (`/start` + тестовий запит)
- [ ] Новий коміт зафіксовано в `update_history.log`
