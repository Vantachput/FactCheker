# 🕵️ AI Fact-Checker — Telegram-бот для виявлення дезінформації

Інтелектуальна система перевірки новин та боротьби з дезінформацією. Бот приймає будь-який текст або переслане повідомлення та повертає деталізований вердикт на основі аналізу перевірених медіа-джерел та моделей штучного інтелекту.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
[![Docs](https://img.shields.io/badge/Docs-GitHub%20Pages-brightgreen)](https://vantachput.github.io/FactCheker/)
[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub%20Actions-orange?logo=github-actions)](https://github.com/Vantachput/FactCheker/actions)

---

## 🌐 Документація (GitHub Pages)

Автоматично згенерована HTML-документація доступна за посиланням:
> **https://vantachput.github.io/FactCheker/**

Документація оновлюється автоматично при кожному `git push` до гілки `main` завдяки CI/CD (GitHub Actions + Sphinx).

---

## ⚡ Quick Start

> Для тих, хто вже має Python 3.12+ та Git встановлені.

```bash
# 1. Клонувати репозиторій
git clone https://github.com/Vantachput/FactCheker.git
cd FactCheker

# 2. Створити та активувати віртуальне середовище
python -m venv .venv
.\.venv\Scripts\Activate        # Windows
# source .venv/bin/activate     # Linux / macOS

# 3. Встановити залежності
pip install -r requirements.txt

# 4. Створити файл .env з токенами (дивись розділ нижче)
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / macOS
# Відредагуйте .env і вставте свої ключі

# 5. Запустити бота
python main.py
```

---

## 📋 Покрокова інструкція для нового розробника

### Крок 0 — Необхідне програмне забезпечення

Перед початком встановіть наступні програми (якщо вони ще не встановлені):

| Програма | Версія | Посилання |
|---|---|---|
| **Python** | ≥ 3.12 | https://www.python.org/downloads/ |
| **Git** | будь-яка | https://git-scm.com/downloads |
| **pip** | ≥ 23 (входить у Python) | оновлюється командою нижче |

#### Встановлення Python (Windows)
1. Перейдіть на https://www.python.org/downloads/ та завантажте останній Python 3.12+.
2. Запустіть інсталятор. **Обов'язково** поставте галочку `Add Python to PATH`.
3. Перевірте встановлення:
   ```bash
   python --version   # Python 3.12.x
   pip --version
   ```

#### Встановлення Git (Windows)
1. Перейдіть на https://git-scm.com/downloads та завантажте Git for Windows.
2. Встановіть з параметрами за замовчуванням.
3. Перевірте:
   ```bash
   git --version   # git version 2.x.x
   ```

---

### Крок 1 — Клонування репозиторію

```bash
git clone https://github.com/Vantachput/FactCheker.git
cd FactCheker
```

---

### Крок 2 — Налаштування віртуального середовища

Рекомендується ізолювати залежності проєкту у віртуальне середовище.

```bash
# Створення
python -m venv .venv

# Активація — Windows (PowerShell / CMD)
.\.venv\Scripts\Activate

# Активація — Linux / macOS
source .venv/bin/activate
```

> Після активації ваш термінал покаже `(.venv)` на початку рядка.

Оновіть pip до актуальної версії:
```bash
python -m pip install --upgrade pip
```

---

### Крок 3 — Встановлення залежностей

```bash
pip install -r requirements.txt
```

Основні бібліотеки, що встановлюються:

| Бібліотека | Призначення |
|---|---|
| `python-telegram-bot` | Telegram Bot API |
| `openai` | Клієнт OpenAI (GPT-4o) |
| `together` | Клієнт Together AI (Llama) |
| `aiohttp` | Асинхронні HTTP-запити |
| `python-dotenv` | Завантаження змінних середовища з `.env` |
| `aiosqlite` | Асинхронна робота з SQLite |
| `pytest` + `pytest-asyncio` | Тестування |
| `ruff` | Лінтинг та форматування |

---

### Крок 4 — Налаштування змінних середовища (`.env`)

Скопіюйте приклад файлу конфігурації:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

> Якщо файл `.env.example` відсутній — створіть файл `.env` вручну.

Відредагуйте `.env` та заповніть усі значення:

```env
# ================================================================
# Telegram
# ================================================================
BOT_TOKEN=your_telegram_bot_token         # Отримати у @BotFather

# ================================================================
# AI провайдери
# ================================================================
OPENAI_API_KEY=your_openai_key            # https://platform.openai.com/api-keys
TOGETHER_API_KEY=your_together_key        # https://api.together.xyz/settings/api-keys
PERPLEXITY_API_KEY=your_perplexity_key   # https://www.perplexity.ai/settings/api

# ================================================================
# Пошук (Google через Serper)
# ================================================================
SERPER_API_KEY=your_serper_key            # https://serper.dev/api-key

# ================================================================
# Назви моделей
# ================================================================
MODEL_NAME=gpt-4o-mini
MODEL_GPT_4_1_mini=ft:gpt-4o-mini:...    # Ваша fine-tuned модель (якщо є)
MODEL_TOGETHER_FT=meta-llama/Llama-3.1-8B-Instruct-Turbo

# ================================================================
# Адмін (Telegram user_id — для необмеженого доступу)
# ================================================================
ADMIN_ID=your_telegram_user_id
```

#### Як отримати API-ключі

| Сервіс | Кроки |
|---|---|
| **Telegram Bot Token** | Відкрийте [@BotFather](https://t.me/BotFather) → `/newbot` → скопіюйте токен |
| **OpenAI** | Зайдіть на [platform.openai.com](https://platform.openai.com/api-keys) → Create new secret key |
| **Together AI** | Зайдіть на [api.together.xyz](https://api.together.xyz/settings/api-keys) → Create an API key |
| **Perplexity** | Зайдіть на [perplexity.ai](https://www.perplexity.ai/settings/api) → Generate |
| **Serper (Google)** | Зайдіть на [serper.dev](https://serper.dev) → Sign in → Get API key |

---

### Крок 5 — База даних

Проєкт використовує **SQLite** — файлова база даних, яка **не потребує встановлення окремого сервера**.

База даних `bot_data.db` **створюється автоматично** при першому запуску бота (функція `init_db()` в `database/db_manager.py`). Жодних додаткових налаштувань не потрібно.

```
bot_data.db
└── таблиця `usage`  — зберігає денні ліміти використання AI-моделей
```

> Файл `bot_data.db` додано до `.gitignore` і не відстежується у Git.

---

### Крок 6 — Запуск у режимі розробки

```bash
python main.py
```

Після успішного запуску ви побачите у терміналі:

```
🚀 Бот запущений асинхронно...
```

Бот тепер слухає повідомлення через Telegram polling. Зупинити — `Ctrl + C`.

---

## 🧰 Базові команди та операції

### Запуск та зупинка

| Дія | Команда |
|---|---|
| Запустити бота | `python main.py` |
| Зупинити бота | `Ctrl + C` |

### Тести

```bash
# Запустити всі тести
pytest

# З виводом покриття коду
pytest --cov=. --cov-report=term-missing

# Запустити конкретний тест-файл
pytest tests/test_filter_sources.py -v
```

### Лінтинг і форматування

```bash
# Перевірити стиль коду (Ruff)
ruff check .

# Автоматично виправити виправні помилки
ruff check --fix .

# Відформатувати код (Black-сумісний форматер)
ruff format .
```

### Документація (Sphinx)

```bash
# Локальна збірка HTML-документації (українська)
cd docs
python -m sphinx -b html source build/html

# Локальна збірка (англійська)
python -m sphinx -b html source_en build/html_en

# Відкрити результат (Windows)
start build\html\index.html
```

### Безпека

```bash
# Аналіз вразливостей у коді (Bandit)
bandit -r . --exclude .venv,tests

# Перевірка залежностей на відомі вразливості (Safety)
safety check -r requirements.txt
```

### Git — типовий робочий процес

```bash
git checkout -b feature/my-feature   # Створити нову гілку
git add .
git commit -m "feat: опис змін"
git push origin feature/my-feature
# Відкрийте Pull Request на GitHub
```

---

## ⚙️ Принцип роботи (Архітектура)

Бот використовує **гібридну архітектуру** з кількома AI-провайдерами, між якими користувач може перемикатися:

```
Користувач
    │
    ▼
[Telegram API]
    │
    ▼
[command_handlers / callback_handlers] ──► [user_states dict]
    │
    ▼
[message_handlers: handle_message]
    │
    ├── Метод "base" (RAG-пайплайн) ──────► [generate_search_query]
    │                                              │
    │                                              ▼
    │                                       [serper_search] ──► Google
    │                                              │
    │                                              ▼
    │                                       [filter_sources]
    │                                        (verified / unverified)
    │                                              │
    │                                              ▼
    │                                       [call_base_gpt] (OpenAI)
    │
    ├── Метод "together" ──────────────────► [call_together] (Llama 3.1)
    ├── Метод "openai_ft" ─────────────────► [call_openai_ft] (Fine-Tuned GPT)
    └── Методи "sonar-*" ──────────────────► [call_perplexity] (Perplexity AI)
```

---

## 📁 Структура проєкту

```
FactCheker/
├── main.py                   # Точка входу, запуск бота
├── requirements.txt          # Залежності проєкту
├── pyproject.toml            # Конфігурація проєкту (ruff, setuptools)
├── pytest.ini                # Конфігурація тестів
├── .env                      # Змінні середовища (НЕ комітити!)
├── .env.example              # Шаблон .env для розробників
├── database/
│   └── db_manager.py         # SQLite: ліміти використання
├── handlers/
│   ├── command_handlers.py   # Обробка /start
│   ├── callback_handlers.py  # Обробка кнопок меню
│   └── message_handlers.py   # Головна логіка перевірки новин
├── services/
│   ├── ai_service.py         # Виклики LLM (OpenAI, Together, Perplexity)
│   └── search_service.py     # Пошук Google через Serper API
├── utils/
│   ├── helpers.py            # Утиліти: розбиття тексту, час, escaping
│   ├── keyboards.py          # Telegram inline-клавіатури
│   └── logger.py             # Логування та підрахунок вартості запитів
├── tests/                    # Модульні тести (pytest)
├── docs/
│   ├── source/               # Sphinx .rst (UA)
│   ├── source_en/            # Sphinx .rst (EN)
│   └── build/                # Локально згенерований HTML (не в Git)
└── .github/workflows/
    └── docs.yml              # CI/CD: автоматична публікація на GitHub Pages
```

---

## 🧠 Ключові функції та модулі

### `main.py`
| Функція | Опис |
|---|---|
| `main()` | Ініціалізує БД, реєструє обробники та запускає polling. Реалізує graceful shutdown з коректним закриттям AI-сесій та БД. |
| `start_wrapper()`, `callback_wrapper()`, `message_wrapper()` | Обгортки для передачі спільного об'єкта `user_states` в обробники. |

---

### `services/ai_service.py`
Ядро AI системи. Абстрагує роботу з трьома провайдерами.

| Функція | Опис |
|---|---|
| `generate_search_query(user_text, model_id)` | **"Search Query Architect"**: перетворює емоційний текст на нейтральний пошуковий запит. |
| `call_base_gpt(claim, verified_srcs, unverified_srcs, model_id, user_id)` | Реалізує **RAG**: передає AI відфільтровані джерела двох рівнів довіри. Вердикт: ПРАВДА / МАНІПУЛЯЦІЯ / ФЕЙК / НЕПІДТВЕРДЖЕНО. |
| `call_perplexity(claim, method, api_key, user_id)` | Викликає моделі серії **Sonar** (з вбудованим пошуком). |
| `call_together(claim, model_id, uid)` | Надсилає запит до **Together AI** (Llama 3.1). |
| `call_openai_ft(claim, model_id, user_id)` | Надсилає запит до **fine-tuned моделі OpenAI**. |

---

### `services/search_service.py`

| Функція / Константа | Опис |
|---|---|
| `SOURCES` | Словник з трьома рівнями надійності: **A+** (gov.ua), **A** (Reuters, BBC), **B** (Суспільне, Guardian). |
| `serper_search(query, api_key)` | Асинхронний пошук Google через Serper.dev API (`gl=ua`, `hl=uk`). |
| `filter_sources(results)` | Розділяє результати на `verified` та `unverified`. |

---

### `database/db_manager.py`

| Функція / Константа | Опис |
|---|---|
| `LIMITS` | Словник із денними лімітами. `sonar-deep-research: 0` (вимкнено), `sonar-reasoning-pro: 1`. |
| `init_db()` | Відкриває постійне з'єднання з `bot_data.db` та створює таблицю `usage`. |
| `check_and_increment_limit(user_id, model_name, admin_id)` | Перевіряє денний ліміт. Адмін — необмежений. |
| `close_db()` | Коректно закриває з'єднання. |

---

## 📚 Стандарти документування

Проєкт використовує **Google Style Docstrings (PEP 257)**.

```python
def my_function(param: str) -> bool:
    """Короткий однорядковий опис.

    Args:
        param (str): Опис параметру.

    Returns:
        bool: Опис значення, що повертається.

    Examples:
        >>> my_function("test")
        True
    """
```

**Правила для контриб'юторів:**
1. Усі публічні функції та класи **зобов'язані** мати docstring.
2. Перед комітом перевіряйте стиль: `ruff check .`
3. Для запуску doctest-тестів: `python -m doctest utils/helpers.py -v`
4. Для генерації документації локально: `cd docs && python -m sphinx -b html source build/html`

---

## ❓ Часті проблеми (FAQ)

**Q: `ModuleNotFoundError` при запуску.**
> Перевірте, що віртуальне середовище активовано (`(.venv)` у терміналі) та залежності встановлені (`pip install -r requirements.txt`).

**Q: `python: command not found` або `python3` потрібен.**
> На деяких системах Python 3 доступний лише як `python3`. Використовуйте `python3 main.py` та `python3 -m venv .venv`.

**Q: Помилка `BOT_TOKEN не знайдено` або `NoneType`.**
> Переконайтесь, що файл `.env` існує в кореневій папці проєкту та містить усі обов'язкові ключі.

**Q: `ruff check .` повертає помилки.**
> Спробуйте `ruff check --fix .` для автовиправлення. Решту виправте вручну згідно з рекомендаціями.

**Q: Тести падають з `asyncio` помилками.**
> Перевірте `pytest.ini` — має бути `asyncio_mode = auto`. Встановіть: `pip install pytest-asyncio`.