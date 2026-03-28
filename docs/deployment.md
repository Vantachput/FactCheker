# Deployment Guide — FactChecker Production Environment

**Аудиторія:** Release Engineer / DevOps  
**Версія проєкту:** 0.1.0  
**Стек:** Python 3.12 · python-telegram-bot · SQLite · aiohttp  
**Режим роботи:** long-polling Telegram Bot (stateful async process)

---

## Зміст

1. [Вимоги до апаратного забезпечення](#1-вимоги-до-апаратного-забезпечення)
2. [Необхідне програмне забезпечення](#2-необхідне-програмне-забезпечення)
3. [Налаштування мережі](#3-налаштування-мережі)
4. [Конфігурація сервера](#4-конфігурація-сервера)
5. [Налаштування бази даних](#5-налаштування-бази-даних)
6. [Розгортання коду](#6-розгортання-коду)
7. [Перевірка працездатності](#7-перевірка-працездатності)

---

## 1. Вимоги до апаратного забезпечення

### Архітектура

- **Підтримувані:** `x86_64` (AMD64), `aarch64` (ARM64 / AWS Graviton)
- **Не підтримується:** `i386` (32-bit)

### Мінімальні вимоги

| Ресурс | Мінімум | Рекомендовано (prod) |
|---|---|---|
| **CPU** | 1 vCPU | 2 vCPU |
| **RAM** | 512 MB | 1 GB |
| **Диск** | 5 GB | 20 GB |
| **ОС** | Ubuntu 22.04 LTS | Ubuntu 24.04 LTS |

> **Примітка.** Бот є I/O-bound процесом: більшість часу він чекає відповідей від Telegram API та зовнішніх AI-сервісів. CPU не є вузьким місцем. RAM-споживання зростає при великій кількості одночасних користувачів через `user_states` dict та `aiohttp`-сесію.

### Розмір дискового простору

| Директорія | Розмір |
|---|---|
| Код проєкту | ~5 MB |
| Python venv + залежності | ~700 MB |
| `bot_data.db` (SQLite) | ~1–50 MB (залежно від кількості користувачів) |
| `bot_usage.log` / `usage_analytics.jsonl` | ~1–500 MB на рік |

Рекомендується налаштувати **logrotate** для ротації лог-файлів (div. Крок 4.3).

---

## 2. Необхідне програмне забезпечення

### Операційна система

Ubuntu 22.04 LTS або Ubuntu 24.04 LTS (рекомендовано).

### Системні пакети

```bash
sudo apt-get update && sudo apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    git \
    curl \
    logrotate \
    ufw
```

Перевірити версії:

```bash
python3.12 --version   # Python 3.12.x
git --version          # git version 2.x.x
```

> **SQLite** постачається разом із Python і додаткової установки **не потребує**.

### Опціонально (рекомендовано для prod)

| Інструмент | Призначення | Встановлення |
|---|---|---|
| `supervisor` або `systemd` | Управління процесом бота | вбудовано / `apt install supervisor` |
| `logrotate` | Ротація логів | `apt install logrotate` |
| `fail2ban` | Захист від brute-force SSH | `apt install fail2ban` |

---

## 3. Налаштування мережі

### Вхідний трафік (Inbound)

Бот використовує **long-polling** — він сам звертається до Telegram, а не навпаки. Відкривати вхідні порти для бота **не потрібно**.

| Порт | Протокол | Призначення | Дія |
|---|---|---|---|
| 22 | TCP | SSH (адміністрування) | Дозволити тільки з trusted IP |

### Вихідний трафік (Outbound)

Сервер повинен мати доступ до наступних зовнішніх endpoint'ів:

| Хост | Порт | Сервіс |
|---|---|---|
| `api.telegram.org` | 443/TCP | Telegram Bot API |
| `api.openai.com` | 443/TCP | OpenAI (GPT-4o) |
| `api.together.xyz` | 443/TCP | Together AI (Llama) |
| `api.perplexity.ai` | 443/TCP | Perplexity AI (Sonar) |
| `google.serper.dev` | 443/TCP | Serper (Google Search) |
| `pypi.org`, `files.pythonhosted.org` | 443/TCP | Pip (тільки при деплої) |

### Налаштування UFW (Uncomplicated Firewall)

```bash
# Скинути правила та встановити безпечні дефолти
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Дозволити SSH тільки з вашого IP
sudo ufw allow from <YOUR_ADMIN_IP> to any port 22 proto tcp

# Увімкнути фаєрвол
sudo ufw enable
sudo ufw status
```

---

## 4. Конфігурація сервера

### 4.1 Створення системного користувача

Бот повинен працювати від **непривілейованого** користувача:

```bash
sudo useradd --system --shell /bin/bash --home /opt/factchecker factbot
sudo mkdir -p /opt/factchecker
sudo chown factbot:factbot /opt/factchecker
```

### 4.2 Налаштування systemd-сервісу (рекомендовано)

Створіть unit-файл сервісу:

```bash
sudo nano /etc/systemd/system/factchecker.service
```

Вміст файлу:

```ini
[Unit]
Description=FactChecker AI Telegram Bot
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=60
StartLimitBurst=5

[Service]
Type=simple
User=factbot
Group=factbot
WorkingDirectory=/opt/factchecker/app
EnvironmentFile=/opt/factchecker/app/.env
ExecStart=/opt/factchecker/venv/bin/python main.py
Restart=on-failure
RestartSec=10s

# Безпека процесу
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/factchecker/app

# Логування
StandardOutput=journal
StandardError=journal
SyslogIdentifier=factchecker

[Install]
WantedBy=multi-user.target
```

Активація:

```bash
sudo systemctl daemon-reload
sudo systemctl enable factchecker.service
sudo systemctl start factchecker.service
```

### 4.3 Ротація логів (logrotate)

Бот пише у `bot_usage.log` та `usage_analytics.jsonl`. Налаштуйте ротацію:

```bash
sudo nano /etc/logrotate.d/factchecker
```

```
/opt/factchecker/app/bot_usage.log
/opt/factchecker/app/usage_analytics.jsonl {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
```

---

## 5. Налаштування бази даних

Проєкт використовує **SQLite** — вбудовану файлову базу даних. Окремий СУБД-сервер **не потрібен**.

### 5.1 Розташування та права доступу

База даних `bot_data.db` створюється автоматично при першому запуску у директорії проєкту. Переконайтесь, що користувач `factbot` має права запису:

```bash
# Після першого деплою, якщо файл ще не існує — він буде створений автоматично
ls -la /opt/factchecker/app/bot_data.db
# Очікуваний вивід:
# -rw-r--r-- 1 factbot factbot 12288 Mar 28 09:00 bot_data.db
```

### 5.2 Структура бази даних

```sql
-- Таблиця створюється автоматично функцією init_db()
CREATE TABLE IF NOT EXISTS usage (
    user_id   INTEGER NOT NULL,
    model     TEXT    NOT NULL,
    date      TEXT    NOT NULL,
    count     INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, model, date)
);
```

### 5.3 Резервне копіювання

SQLite підтримує **«онлайн» резервне копіювання** без зупинки бота:

```bash
# Зробити резервну копію вручну
sqlite3 /opt/factchecker/app/bot_data.db ".backup /opt/factchecker/backups/bot_data_$(date +%Y%m%d).db"
```

Автоматизація через cron (щодня о 03:00):

```bash
sudo -u factbot crontab -e
# Додати рядок:
0 3 * * * sqlite3 /opt/factchecker/app/bot_data.db ".backup /opt/factchecker/backups/bot_data_$(date +\%Y\%m\%d).db"
```

> Зберігайте резервні копії за межами сервера (S3, Google Cloud Storage тощо).

---

## 6. Розгортання коду

### 6.1 Перше розгортання

```bash
# Переключитись на системного користувача
sudo -i -u factbot

# Клонувати репозиторій
git clone https://github.com/Vantachput/FactCheker.git /opt/factchecker/app
cd /opt/factchecker/app

# Створити віртуальне середовище
python3.12 -m venv /opt/factchecker/venv

# Встановити залежності
/opt/factchecker/venv/bin/pip install --upgrade pip
/opt/factchecker/venv/bin/pip install -r requirements.txt

# Створити файл змінних середовища
cp .env.example .env
nano .env   # Заповнити всі значення (BOT_TOKEN, API-ключі тощо)

# Вийти з factbot-сесії
exit

# Запустити сервіс
sudo systemctl start factchecker.service
```

### 6.2 Оновлення (Zero-downtime update)

```bash
sudo -i -u factbot

cd /opt/factchecker/app

# Завантажити зміни
git pull origin main

# Оновити залежності (якщо requirements.txt змінився)
/opt/factchecker/venv/bin/pip install -r requirements.txt

exit

# Перезапустити сервіс
sudo systemctl restart factchecker.service
```

### 6.3 Відкат до попередньої версії

```bash
sudo -i -u factbot
cd /opt/factchecker/app

# Переглянути останні коміти
git log --oneline -10

# Відкатитись до конкретного коміту
git checkout <commit-hash>

exit
sudo systemctl restart factchecker.service
```

### 6.4 Змінні середовища у production

**Ніколи не зберігайте `.env` у репозиторії.** Файл `.env` знаходиться у `.gitignore`.

Обов'язкові змінні для production:

```env
BOT_TOKEN=<telegram_bot_token>
OPENAI_API_KEY=<openai_key>
TOGETHER_API_KEY=<together_key>
PERPLEXITY_API_KEY=<perplexity_key>
SERPER_API_KEY=<serper_key>
MODEL_NAME=gpt-4o-mini
MODEL_TOGETHER_FT=meta-llama/Llama-3.1-8B-Instruct-Turbo
ADMIN_ID=<telegram_user_id_of_admin>
```

Права доступу до `.env` файлу:

```bash
chmod 600 /opt/factchecker/app/.env
chown factbot:factbot /opt/factchecker/app/.env
```

---

## 7. Перевірка працездатності

### 7.1 Статус systemd-сервісу

```bash
sudo systemctl status factchecker.service
```

Очікуваний вивід:

```
● factchecker.service - FactChecker AI Telegram Bot
     Loaded: loaded (/etc/systemd/system/factchecker.service; enabled)
     Active: active (running) since ...
   Main PID: 12345 (python)
```

### 7.2 Перевірка логів (journald)

```bash
# Останні 50 рядків логів
sudo journalctl -u factchecker.service -n 50

# Стрімінг логів у реальному часі
sudo journalctl -u factchecker.service -f
```

Ознаки **успішного запуску** у логах:

```
🚀 Бот запущений асинхронно...
```

Ознаки **проблем** у логах:

| Повідомлення | Причина | Дія |
|---|---|---|
| `Unauthorized` / `401` | Невірний `BOT_TOKEN` | Перевірити `.env` |
| `Invalid API key` | Невірний ключ AI-провайдера | Перевірити `.env` |
| `ConnectionError` | Немає доступу до зовнішнього API | Перевірити outbound firewall |
| `PermissionError` on `bot_data.db` | Невірні права на файл | `chown factbot:factbot bot_data.db` |

### 7.3 Функціональна перевірка

1. Відкрийте бота у Telegram.
2. Надішліть команду `/start`.
3. Переконайтесь, що бот відповів привітальним повідомленням та показав меню вибору методу.
4. Надішліть будь-який новинний текст.
5. Отримайте вердикт (ПРАВДА / МАНІПУЛЯЦІЯ / ФЕЙК / НЕПІДТВЕРДЖЕНО).

### 7.4 Перевірка ресурсів

```bash
# Споживання CPU та RAM процесом бота
ps aux | grep python

# Розмір бази даних
du -sh /opt/factchecker/app/bot_data.db

# Розмір логів
du -sh /opt/factchecker/app/bot_usage.log
du -sh /opt/factchecker/app/usage_analytics.jsonl

# Вільне місце на диску
df -h /opt/factchecker
```

### 7.5 Перевірка доступності зовнішніх API

```bash
# Telegram API
curl -s https://api.telegram.org | head -1

# OpenAI
curl -s -o /dev/null -w "%{http_code}" https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
# Очікуємо: 200

# Serper
curl -s -o /dev/null -w "%{http_code}" https://google.serper.dev/search \
  -H "X-API-KEY: $SERPER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"q":"test"}'
# Очікуємо: 200
```

---

## Додаток A — Корисні команди для підтримки

```bash
# Перезапуск бота
sudo systemctl restart factchecker.service

# Зупинка бота
sudo systemctl stop factchecker.service

# Перегляд помилок за останню годину
sudo journalctl -u factchecker.service --since "1 hour ago" -p err

# Ручне резервне копіювання БД
sqlite3 /opt/factchecker/app/bot_data.db ".backup /tmp/bot_data_backup.db"
```

---

## Додаток B — Checklist перед запуском у production

- [ ] Сервер запущено з ОС Ubuntu 22.04+ LTS
- [ ] Системний користувач `factbot` створено
- [ ] Репозиторій клоновано у `/opt/factchecker/app`
- [ ] Python venv створено та залежності встановлено
- [ ] Файл `.env` заповнено та права `600` встановлено
- [ ] UFW налаштовано (SSH обмежено, outbound відкрито)
- [ ] systemd unit-файл створено та увімкнено (`systemctl enable`)
- [ ] Бот запущено (`systemctl start`) та статус `active (running)`
- [ ] Функціональна перевірка пройдена (відповідь на `/start` та тестовий запит)
- [ ] logrotate налаштовано
- [ ] Резервне копіювання БД налаштовано через cron
