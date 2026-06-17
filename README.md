# 🕵️ AI Fact-Checker — Telegram-бот для виявлення дезінформації

Telegram-бот, що приймає текст, переслані повідомлення, зображення, аудіо, відео, кружечки та посилання на Threads — і повертає вердикт на основі перевірених медіа-джерел та моделей ШІ.

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)
[![Docs](https://img.shields.io/badge/Docs-GitHub%20Pages-brightgreen)](https://vantachput.github.io/FactCheker/)
[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub%20Actions-orange?logo=github-actions)](https://github.com/Vantachput/FactCheker/actions)

---

## ⚡ Quick Start

```bash
git clone https://github.com/Vantachput/FactCheker.git
cd FactCheker
python -m venv .venv
.\.venv\Scripts\Activate        # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
copy .env.example .env          # Windows (cp для Linux/macOS)
# Відредагуйте .env — вставте свої API-ключі
python main.py
```

> [!NOTE]
> FFmpeg постачається автоматично через `imageio-ffmpeg` — окремо встановлювати не потрібно.

---

## 📋 Встановлення

### Передумови

| Програма | Версія |
|---|---|
| Python | ≥ 3.12 |
| Git | будь-яка |

### Крок 1 — Клонування та середовище

```bash
git clone https://github.com/Vantachput/FactCheker.git
cd FactCheker

python -m venv .venv
.\.venv\Scripts\Activate        # Windows
# source .venv/bin/activate     # Linux / macOS

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Крок 2 — Змінні середовища

```bash
copy .env.example .env          # Windows
# cp .env.example .env          # Linux / macOS
```

Відредагуйте `.env` — заповніть необхідні ключі:

```env
# Telegram
BOT_TOKEN=your_telegram_bot_token         # @BotFather

# AI провайдери
OPENAI_API_KEY=your_openai_key            # platform.openai.com
TOGETHER_API_KEY=your_together_key        # api.together.xyz
PERPLEXITY_API_KEY=your_perplexity_key    # perplexity.ai/settings/api
OpenRouter_API=your_openrouter_key        # openrouter.ai (відеоаналіз Qwen)
DEEPGRAM_API_KEY=your_deepgram_key        # console.deepgram.com (транскрипція)

# Threads API
THREADS_ACCESS_TOKEN=your_threads_access_token
THREADS_APP_ID=your_threads_app_id
THREADS_API_VERSION=v1.0

# Пошук
SERPER_API_KEY=your_serper_key            # serper.dev

# Моделі
MODEL_NAME=gpt-5-mini
MODEL_PREVIEW=gpt-4o-mini-search-preview
MODEL_GPT_4_1_mini=ft:gpt-4o-mini:...     # Fine-tuned OpenAI
MODEL_TOGETHER_FT=gemma-3-12b-it-...      # Fine-tuned Gemma
MODEL_TOGETHER_FT_2=Meta-Llama-3.1-...    # Fine-tuned Llama

# Адмін
ADMIN_ID=your_telegram_user_id
```

### Крок 3 — Запуск

```bash
python main.py
```

> База даних SQLite (`bot_data.db`) створюється автоматично при першому запуску.

---

## ⚙️ Архітектура

```
Користувач → Telegram API → Бот
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
    [Медіа-вхід]        [Текст/Репост]      [Threads URL]
    Голос → Deepgram     │                  ThreadsService
    Фото → GPT Vision    │                       │
    Відео → Qwen 3.6     │                       │
         │                ▼                       │
         └──────→  Формування claim  ←────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         [Fine-tuned] [Base RAG] [Perplexity]
         Together AI   Serper →   Sonar /
         OpenAI FT     GPT        Reasoning /
                                  Deep Research
                         │
                    Вердикт + джерела
```

**Методи аналізу:**

| Категорія | Метод | Модель |
|---|---|---|
| Base (RAG) | `base` | Serper → GPT-5-mini |
| Fine-tuned | `together` | Llama 3.1 8B |
| Fine-tuned | `together_gemma` | Gemma 3 12B |
| Fine-tuned | `openai_ft` | GPT-4o-mini FT |
| Web-search | `sonar` | Perplexity Sonar |
| Web-search | `sonar-reasoning-pro` | Perplexity Reasoning Pro |
| Web-search | `sonar-deep-research` | Perplexity Deep Research |

**Денні ліміти** (налаштовані у `database/db_manager.py`):

| Метод | Ліміт |
|---|---|
| `sonar`, Base, Fine-tuned | безлімітно |
| `sonar-reasoning-pro` | 1 / день |
| `sonar-deep-research` | вимкнено (тільки адмін) |

> [!TIP]
> Користувач з `ADMIN_ID` має необмежений доступ до всіх моделей. Ліміти обнуляються щоденно о 00:00.

---

## 🗂️ Структура проєкту

```
FactCheker/
├── main.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Makefile
├── Procfile
├── pytest.ini
├── LICENSE.txt
├── database/
│   └── db_manager.py
├── handlers/
│   ├── command_handlers.py
│   ├── callback_handlers.py
│   └── message_handlers.py
├── services/
│   ├── ai_service.py
│   ├── search_service.py
│   ├── deepgram_service.py
│   └── threads_service.py
├── utils/
│   ├── helpers.py
│   ├── keyboards.py
│   └── logger.py
├── scripts/
├── tests/
├── profiling/
└── docs/
```

---

## 🧰 Makefile команди

| Команда | Дія |
|---|---|
| `make dev` | Запуск бота |
| `make test` | Юніт-тести (pytest) |
| `make test-cov` | Тести з покриттям |
| `make lint` | Перевірка стилю (Ruff) |
| `make lint-fix` | Автовиправлення стилю |
| `make format` | Форматування коду |
| `make docs` | Збірка Sphinx документації |
| `make profile` | Профайлінг швидкодії |
| `make backup` | Бекап БД |
| `make deploy` | Деплой на сервер (Linux) |
| `make restart` | Перезапуск сервісу |
| `make status` | Статус сервісу |
| `make logs` | Логи сервісу |

---

## 🧠 Ключові модулі

### `services/ai_service.py`

| Функція | Призначення |
|---|---|
| `generate_search_query(...)` | Формує пошуковий запит із тексту користувача |
| `call_base_gpt(...)` | RAG-конвеєр: вердикт на основі знайдених джерел |
| `call_perplexity(...)` | Perplexity Sonar з вбудованим пошуком |
| `call_together(...)` | Fine-tuned моделі Together AI |
| `call_openai_ft(...)` | Fine-tuned модель OpenAI |
| `extract_text_from_image(...)` | OCR/аналіз зображень (GPT-4o-mini Vision) |
| `analyze_video_with_together(...)` | Аналіз відео через Qwen (OpenRouter) |
| `extract_factors_from_video_analysis(...)` | Виділення пошукових тез із аналізу відео |

### `services/search_service.py`

| Елемент | Призначення |
|---|---|
| `SOURCES` | Словник довірених доменів (A+, A, B) |
| `serper_search(...)` | Пошук Google через Serper API |
| `filter_sources(...)` | Розподіл результатів на перевірені / неперевірені |

### `services/deepgram_service.py`

| Функція | Призначення |
|---|---|
| `transcribe_audio(...)` | Транскрипція через Deepgram Nova-3 |

### `services/threads_service.py`

| Метод | Призначення |
|---|---|
| `ThreadsService.get_post_data(...)` | Отримання тексту та зображень з постів Threads |
| `ThreadsService.is_token_valid()` | Перевірка актуальності токена |

### `handlers/message_handlers.py`

| Функція | Призначення |
|---|---|
| `handle_message(...)` | Головна логіка: парсинг вхідних даних → вибір методу → вердикт |
| `send_smart_reply(...)` | Надсилання результату частинами (ліміт Telegram 4096 символів) |

### `utils/helpers.py`

| Функція | Призначення |
|---|---|
| `split_text(...)` | Розбиття тексту під ліміт Telegram |
| `get_progress_bar(...)` | Емодзі-прогрес-бар впевненості ШІ |
| `convert_to_wav(...)` | Конвертація аудіо → WAV (FFmpeg) |
| `compress_video(...)` | Стиснення відео → 480p, 5 fps (FFmpeg) |

### `utils/logger.py`

| Функція | Призначення |
|---|---|
| `setup_logging()` | Налаштування логів (консоль + `app.log`) |
| `log_ai_usage(...)` | Логування витрат на токени (TXT + JSONL) |

### `database/db_manager.py`

| Функція | Призначення |
|---|---|
| `init_db()` | Ініціалізація SQLite |
| `check_and_increment_limit(...)` | Облік та перевірка денних лімітів |
| `close_db()` | Закриття з'єднання |

---

## 📚 Стандарти коду

- **Docstrings**: Google Style (PEP 257)
- **Лінтер**: Ruff (`E`, `F`, `I`, `PERF`, `D`)
- **Тести**: pytest + pytest-asyncio (`asyncio_mode = auto`)

---

## 🌐 Документація

Автогенерована HTML-документація (Sphinx): **https://vantachput.github.io/FactCheker/**

Оновлюється при кожному `push` до `main` через GitHub Actions.

---

## ❓ FAQ

**Q: `ModuleNotFoundError` при запуску.**
> Перевірте активацію `(.venv)` та `pip install -r requirements.txt`.

**Q: `BOT_TOKEN не знайдено`.**
> Переконайтесь, що `.env` існує та містить усі ключі.

**Q: Тести падають з `asyncio` помилками.**
> Перевірте `pytest.ini` — має бути `asyncio_mode = auto`.

---

## 📄 Ліцензія

[MIT](LICENSE.txt) © Vantachput
