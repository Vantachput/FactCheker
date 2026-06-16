# 🕵️ AI Fact-Checker — Telegram-бот для виявлення дезінформації

Інтелектуальна система перевірки новин та боротьби з дезінформацією. Бот приймає будь-який текст, переслані повідомлення, зображення (з текстом чи без), аудіозаписи, голосові повідомлення, відео, кружечки, а також посилання на публікації в Threads, та повертає деталізований аналіз і вердикт на основі перевірених медіа-джерел та передових моделей штучного інтелекту.

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

> [!NOTE]
> Для обробки аудіо (конвертація у WAV) та відео (стиснення) проєкт використовує утиліту `ffmpeg`, яка автоматично постачається через бібліотеку `imageio-ffmpeg`. Додатково встановлювати `ffmpeg` у систему не потрібно.

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
| `openai` | Клієнт OpenAI (GPT-4o, GPT-5-mini, Vision) |
| `together` | Клієнт Together AI (Llama, Gemma) |
| `aiohttp` | Асинхронні HTTP-запити |
| `python-dotenv` | Завантаження змінних середовища з `.env` |
| `aiosqlite` | Асинхронна робота з SQLite |
| `pytest` + `pytest-asyncio` | Тестування |
| `ruff` | Лінтинг та форматування коду |
| `imageio-ffmpeg` | Автоматичне завантаження та запуск бінарника FFmpeg для обробки аудіо та відео |
| `aiofiles` | Асинхронна робота з файловою системою (для запису аналітики без блокувань) |
| `pytz` | Коректна робота з часовими поясами (часовий пояс України) |

---

### Крок 4 — Налаштування змінних середовища (`.env`)

Скопіюйте приклад файлу конфігурації:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

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
TOGETHER_NO_BANNER=1                      # Вимкнути консольний банер Together AI

PERPLEXITY_API_KEY=your_perplexity_key    # https://www.perplexity.ai/settings/api
OpenRouter_API=your_openrouter_key        # Ключ OpenRouter (для Qwen відео аналізу): https://openrouter.ai/keys
DEEPGRAM_API_KEY=your_deepgram_key        # Ключ Deepgram (транскрибування аудіо): https://console.deepgram.com/

# ================================================================
# Threads API (для завантаження та аналізу постів Threads)
# ================================================================
THREADS_ACCESS_TOKEN=your_threads_access_token
THREADS_APP_ID=your_threads_app_id
THREADS_API_VERSION=v1.0

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
| **OpenRouter** | Зареєструйтесь на [openrouter.ai](https://openrouter.ai) → Ключі API → Create Key |
| **Deepgram** | Зареєструйтесь на [deepgram.com](https://deepgram.com) → API Keys → Create Key |
| **Threads API** | Налаштуйте доступ через Meta for Developers (Graph API) для отримання токена |

---

### Крок 5 — База даних

Проєкт використовує **SQLite** — локальну файлову базу даних, яка **не потребує встановлення окремого сервера**.

База даних `bot_data.db` **створюється автоматично** при першому запуску бота (функція `init_db()` в `database/db_manager.py`).

```
bot_data.db
└── таблиця `usage`  — зберігає добову активність користувачів щодо використання AI-моделей та лімітів
```

#### 🛡️ Денні ліміти (налаштовані у `database/db_manager.py`)
Бот обмежує кількість щоденних запитів для платних або ресурсномістких моделей Perplexity:
* **`sonar` (Базовий)** — безлімітно (ліміт встановлено на `999999`).
* **`sonar-reasoning-pro`** — `1` запит на день для одного користувача.
* **`sonar-deep-research`** — `0` запитів на день (повністю вимкнено для звичайних користувачів).
* **Базові моделі (`Base`), Fine-tuned та інші** — ліміт `1000000` (фактично безлімітно).

> [!TIP]
> Користувач, чий Telegram ID збігається зі значенням `ADMIN_ID` у файлі `.env`, має **повний та необмежений доступ** до всіх моделей (включаючи `sonar-deep-research`), і лічильник лімітів для нього не збільшується.
> Добові ліміти автоматично оновлюються (обнуляються) о 00:00 кожного дня.

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

Для зручності розробки в проєкті наявний `Makefile` (працює на Windows через Git Bash або утиліту `make`, а також нативно на Linux/macOS).

### Makefile Команди

| Дія | Команда |
|---|---|
| Запустити бота локально | `make dev` або `python main.py` |
| Запустити всі модульні тести | `make test` або `pytest` |
| Запустити тести з покриттям | `make test-cov` |
| Перевірити стиль коду (Ruff) | `make lint` |
| Автоматично виправити помилки стилю | `make lint-fix` |
| Відформатувати код (Ruff) | `make format` |
| Зібрати HTML-документацію Sphinx | `make docs` |
| Запустити профайлінг швидкодії | `make profile` |
| Створити резервну копію бази даних SQLite | `make backup` |
| Деплой оновлень на сервер (Linux) | `make deploy` |
| Перезапустити сервіс бота на сервері | `make restart` |
| Переглянути системний статус бота | `make status` |
| Логи роботи бота на сервері | `make logs` |

---

## ⚙️ Принцип роботи (Архітектура)

Бот використовує **асинхронну гібридну архітектуру** із підтримкою мультимедіа та можливістю вибору AI-провайдерів у налаштуваннях:

```
                  Користувач
                      │
                      ▼
                [Telegram API]
                      │
   ┌──────────────────┼─────────────────────┬──────────────────────┐
   ▼                  ▼                     ▼                      ▼
[Голос/Аудіо]    [Відео/Кружечок]     [Зображення / OCR]    [Посилання Threads]
   │                  │                     │                      │
[convert_to_wav]  [compress_video]    [extract_text_         [ThreadsService]
   │                  │                from_image]                 │
[transcribe_      [analyze_video_       (Vision)            (Текст + Зображення)
 audio]            with_together]           │                      │
(Deepgram)          (Qwen 3.6)              │                      │
   │                  │                     │                      │
   ▼                  ▼                     ▼                      ▼
  Текст             Факти                 Текст                  Текст
   │                  │                     │                      │
   └──────────────────┴──────────┬──────────┴──────────────────────┘
                                 │
                                 ▼
                     [message_handlers.py]
                                 │
       ┌─────────────────────────┼──────────────────────────┐
       ▼                         ▼                          ▼
  Метод "base"            Методи Fine-tuning           Методи "sonar-*"
 (RAG Pipeline)         (Gemma, Llama, OpenAI FT)      (Perplexity API)
       │                         │                          │
[generate_search_query]          │                     [call_perplexity]
       │                         │                     (Вбудований пошук)
[serper_search] (Google)         ├─► call_together          │
       │                         ├─► call_openai_ft         │
[filter_sources]                 │                          │
 (Verified / Unverified)         │                          │
       │                         │                          │
[call_base_gpt] (OpenAI)         │                          │
       │                         │                          │
       └─────────────────────────┼──────────────────────────┘
                                 │
                                 ▼
                         [send_smart_reply]
                     (Розбиття >4000 символів)
                                 │
                                 ▼
                            Користувач
```

### 🔁 Fallback-алгоритм пошуку
Якщо при використанні методу **`base`** згенерований LLM пошуковий запит (алгоритм "Search Query Architect") не дає результатів у Google (наприклад, через надмірну заплутаність чи специфічність твердження), бот автоматично застосовує **Fallback-алгоритм**: бере перші 200 символів оригінального тексту користувача і виконує прямий пошук Google, щоб знайти хоч якісь спростування чи згадки в новинах.

---

## 📁 Структура проєкту

```
FactCheker/
├── main.py                   # Точка входу, запуск бота та graceful shutdown
├── requirements.txt          # Залежності проєкту (pip)
├── pyproject.toml            # Конфігурація ruff, setuptools, метадані
├── pytest.ini                # Налаштування pytest
├── Makefile                  # Таск-раннер для розробника та сервера
├── database/
│   └── db_manager.py         # SQLite: Persistent-з'єднання, облік добових лімітів
├── handlers/
│   ├── command_handlers.py   # Обробка /start
│   ├── callback_handlers.py  # Обробка кнопок меню та довідки
│   └── message_handlers.py   # Логіка обробки тексту, аудіо, відео, зображень та Threads посилань
├── services/
│   ├── ai_service.py         # Ядро взаємодії з ШІ (OpenAI, Together, Perplexity, OpenRouter)
│   ├── search_service.py     # Пошук Google через Serper API, білий список джерел (A+, A, B)
│   ├── deepgram_service.py   # Розпізнавання голосу через Deepgram Nova-3 API
│   └── threads_service.py    # Парсинг та Graph API інтеграція з Threads
├── utils/
│   ├── helpers.py            # Розбиття тексту, емодзі-шкала впевненості ШІ, конвертація аудіо, стиснення відео
│   ├── keyboards.py          # Telegram inline-клавіатури для меню
│   └── logger.py             # Логування та калькуляція фінансових витрат на токени (Text + JSONL)
├── scripts/                  # Допоміжні скрипти автоматизації (PowerShell, Bash)
├── tests/                    # Модульні та інтеграційні тести (pytest)
└── docs/                     # Джерела документації Sphinx (.rst)
```

---

## 🧠 Ключові функції та модулі

### `services/ai_service.py`
Ядро AI системи, яке керує промптингом, роботою з баченням (Vision) та генерацією відповідей.

| Функція | Опис |
|---|---|
| `generate_search_query(user_text, model_id)` | Перетворює емоційний текст користувача на лаконічний пошуковий запит (виділяє "якірні факти"). |
| `call_base_gpt(claim, verified_srcs, unverified_srcs, model_id, user_id, video_analysis)` | Реалізує RAG конвеєр: подає джерела двох рівнів довіри та аналіз відео у контекст моделі OpenAI для вердикту (ПРАВДА / МАНІПУЛЯЦІЯ / ФЕЙК / НЕПІДТВЕРДЖЕНО). |
| `call_perplexity(claim, method, api_key, user_id)` | Викликає моделі серії Perplexity Sonar із вбудованим пошуком у реальному часі. |
| `call_together(claim, model_id, uid)` | Надсилає запити до fine-tuned моделей Together AI (Llama 3.1 8B або gemma-3-12b). |
| `call_openai_ft(claim, model_id, user_id)` | Звертається до fine-tuned моделі OpenAI (`ft:gpt-4o-mini...`). |
| `extract_text_from_image(bot, file_id)` | Зчитує текст або детально аналізує події на зображенні з Telegram за допомогою моделі `gpt-4o-mini` Vision. |
| `analyze_image_from_url(image_url)` | Аналізує зображення за URL-адресою (для картинок із постів Threads). |
| `analyze_video_with_together(video_path)` | Аналізує стиснене відео за допомогою моделі `qwen/qwen3.6-35b-a3b` через OpenRouter. |
| `extract_factors_from_video_analysis(analysis)` | Виділяє ключові пошукові тези на основі текстового опису відео. |

---

### `services/deepgram_service.py`
Асинхронне перетворення аудіофайлів на текст.

| Функція | Опис |
|---|---|
| `transcribe_audio(file_path)` | Надсилає аудіофайл на сервери Deepgram (модель `nova-3`, увімкнене автовизначення мови та інтелектуальне форматування). |

---

### `services/threads_service.py`
Інтеграція з соціальною мережею Threads.

| Метод / Клас | Опис |
|---|---|
| `ThreadsService` | Клас для роботи з API Threads. |
| `is_token_valid()` | Перевіряє актуальність `THREADS_ACCESS_TOKEN`. |
| `get_post_data(url)` | Повертає текст та зображення поста. Якщо ID поста числовий — робить запит до Graph API. Якщо літерний шорткод — скрапить HTML-код сторінки для обходу обмежень Graph API. |

---

### `services/search_service.py`
Робота з пошуковою видачею Google та оцінка надійності сайтів.

| Елемент | Опис |
|---|---|
| `SOURCES` | Словник білих доменів: **A_PLUS** (держ. органи `gov.ua`, НБУ), **A** (BBC, Reuters, Укрінформ), **B** (Суспільне, Liga.net, Pravda). |
| `serper_search(query, api_key)` | Асинхронний пошук Google через Serper.dev API (`gl=ua`, `hl=uk`). |
| `filter_sources(results)` | Сортує отримані URL-адреси на `verified` (якщо домен є в `SOURCES`) та `unverified`. |

---

### `utils/helpers.py`
Корисні утиліти для обробки медіа та тексту.

| Функція | Опис |
|---|---|
| `split_text(text, max_length)` | Безпечно розбиває великий текст на шматки, щоб уникнути ліміту Telegram у 4096 символів. |
| `get_progress_bar(text)` | Парсить відсоток у тексті ШІ (наприклад "85%") і будує гарний візуальний емодзі-прогрес-бар. |
| `convert_to_wav(input_path, output_path)` | Конвертує аудіозапис за допомогою FFmpeg у формат `16kHz, mono, wav` для найкращої якості розпізнавання. |
| `compress_video(input_path, output_path)` | Зменшує роздільну здатність відео до 480p, знижує частоту до 5 кадрів/сек і вирізає звук за допомогою FFmpeg для економії токенів і швидкого надсилання у відеомодель. |

---

### `utils/logger.py`
Централізоване логування та фінансовий моніторинг.

| Функція | Опис |
|---|---|
| `setup_logging()` | Конфігурує логування у консоль та файл `app.log`. |
| `log_ai_usage(method, model_name, usage_data, user_id)` | Асинхронно записує статистику використання токенів та автоматично розраховує фінансову вартість запиту відповідно до актуальних тарифів провайдерів. Записує дані в текстовому вигляді у `bot_usage.log` та у JSONL-вигляді у `usage_analytics.jsonl`. |

---

## 📚 Стандарти документування

Проєкт суворо використовує **Google Style Docstrings (PEP 257)**.

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
2. Перед комітом перевіряйте стиль коду та документації: `make lint` (викликає `ruff check .`).
3. Для тестування прикладів у документації (TDD-підхід): `python -m doctest utils/helpers.py -v`.
4. Для генерації документації локально: `make docs`.

---

## ❓ Часті проблеми (FAQ)

**Q: `ModuleNotFoundError` при запуску.**
> Перевірте, що віртуальне середовище активовано (`(.venv)` у терміналі) та залежності встановлені (`pip install -r requirements.txt`).

**Q: Помилка `BOT_TOKEN не знайдено` або `NoneType`.**
> Переконайтесь, що файл `.env` існує в кореневій папці проєкту та містить усі обов'язкові ключі.

**Q: Тести падають з `asyncio` помилками.**
> Перевірте `pytest.ini` — має бути `asyncio_mode = auto`. Встановіть: `pip install pytest-asyncio`.