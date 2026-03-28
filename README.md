# 🕵️ AI Fact-Checker — Telegram-бот для виявлення дезінформації

Інтелектуальна система перевірки новин та боротьби з дезінформацією. Бот приймає будь-який текст або переслане повідомлення та повертає деталізований вердикт на основі аналізу перевірених медіа-джерел та моделей штучного інтелекту.

---

## 🌐 Документація (GitHub Pages)

Автоматично згенерована HTML-документація доступна за посиланням:
> **https://vantachput.github.io/FactCheker/**

Документація оновлюється автоматично при кожному `git push` до гілки `main` завдяки CI/CD (GitHub Actions + Sphinx).

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

## 🚀 Встановлення та запуск

```bash
# 1. Клонуйте репозиторій
git clone https://github.com/Vantachput/FactCheker.git
cd FactCheker

# 2. Створіть та активуйте віртуальне середовище
python -m venv .venv
.\.venv\Scripts\Activate   # Windows
source .venv/bin/activate  # Linux/macOS

# 3. Встановіть залежності
pip install -r requirements.txt

# 4. Створіть файл .env (на основі прикладу нижче)
# 5. Запустіть бота
python main.py
```

### Файл `.env` (обов'язкові змінні)
```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_key
TOGETHER_API_KEY=your_together_key
SERPER_API_KEY=your_serper_key
PERPLEXITY_API_KEY=your_perplexity_key
MODEL_NAME=gpt-4o-mini
MODEL_GPT_4_1_mini=ft:gpt-4o-mini:...
MODEL_TOGETHER_FT=meta-llama/Llama-3.1-8B-Instruct-Turbo
ADMIN_ID=your_telegram_user_id
```

---

## 📁 Структура проєкту

```
FactCheker/
├── main.py                   # Точка входу, запуск бота
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
├── docs/
│   ├── source/               # Вихідні файли Sphinx (.rst, conf.py)
│   ├── html/                 # Локально згенерований сайт
│   └── generate_docs.md      # Інструкція зі збірки документації
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
| `generate_search_query(user_text, model_id)` | **"Search Query Architect"**: перетворює емоційний текст на нейтральний пошуковий запит, видаляючи "шум" та зберігаючи ключові факти (дати, імена, організації). |
| `call_base_gpt(claim, verified_srcs, unverified_srcs, model_id, user_id)` | Реалізує **RAG (Retrieval-Augmented Generation)**: передає AI відфільтровані джерела двох рівнів довіри. Використовує "Logic Matrix" для визначення вердикту: ПРАВДА / МАНІПУЛЯЦІЯ / ФЕЙК / НЕПІДТВЕРДЖЕНО. |
| `call_perplexity(claim, method, api_key, user_id)` | Викликає моделі серії **Sonar** (deep-research, reasoning-pro). Ці моделі мають власний пошуковий рушій і не потребують Serper. |
| `call_together(claim, model_id, uid)` | Надсилає запит до **Together AI** (Llama 3.1 8B/70B). |
| `call_openai_ft(claim, model_id, user_id)` | Надсилає запит до **fine-tuned моделі OpenAI** (додатково натренованої на прикладах фейків). |
| `get_ai_session()` | Повертає або створює глобальну `aiohttp.ClientSession` для HTTP-запитів. |

---

### `services/search_service.py`
Пошуковий рушій з системою "білих списків" для фільтрації джерел.

| Функція / Константа | Опис |
|---|---|
| `SOURCES` | Словник з трьома рівнями надійності: **A+** (офіційні .gov.ua), **A** (Reuters, BBC, Ukrinform), **B** (Суспільне, Правда України, Guardian). |
| `serper_search(query, api_key)` | Асинхронний пошук Google через Serper.dev API. Налаштовано на пріоритет українського контенту (`gl=ua`, `hl=uk`). |
| `filter_sources(results)` | Розділяє результати пошуку на `verified` (з "білого списку") та `unverified`. Саме цей поділ дозволяє AI спиратися на надійні дані. |
| `get_domain(url)` | Витягує чисте доменне ім'я з URL (наприклад, `bbc.com` з `https://www.bbc.com/news`). |

---

### `handlers/message_handlers.py`
Головна бізнес-логіка обробки запиту від користувача.

| Функція | Опис |
|---|---|
| `handle_message(update, context, user_states)` | Основний диспетчер. Парсить тип повідомлення (текст, репост з каналу/групи/користувача), перевіряє ліміти та викликає відповідний AI-сервіс. Реалізує **Fallback-алгоритм**: якщо "розумний" запит не дає результатів, автоматично надсилає прямий текст до Google. |
| `send_smart_reply(update, text, status_msg)` | Відправляє відповідь частинами (якщо > 4000 символів), вмикаючи Link Preview тільки для першого повідомлення. |

---

### `database/db_manager.py`
Управління SQLite для денних лімітів використання платних моделей.

| Функція / Константа | Опис |
|---|---|
| `LIMITS` | Словник із денними лімітами на модель. `sonar-deep-research: 0` (вимкнено), `sonar-reasoning-pro: 1`. |
| `init_db()` | Відкриває **постійне** (persistent) з'єднання з `bot_data.db` та створює таблицю `usage`. |
| `check_and_increment_limit(user_id, model_name, admin_id)` | Перевіряє, чи не вичерпав користувач денний ліміт. Адміністратор має необмежений доступ. Автоматично скидає лічильники на початку нового дня. |
| `close_db()` | Коректно закриває з'єднання при зупинці бота. |

---

### `utils/helpers.py`
Чисті утиліти (pure functions) без залежностей від стану бота.

| Функція | Опис |
|---|---|
| `split_text(text, max_length)` | Розбиває великий текст на фрагменти (за замовчуванням 4000 символів) для Telegram API. |
| `get_progress_bar(text)` | Знаходить у тексті відсоток впевненості AI (напр. `87%`) і генерує візуальну шкалу з емодзі 🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜. |
| `escape_markdown(text)` | Екранує спеціальні символи `_`, `*`, `[` для безпечного рендеру в Telegram (`ParseMode.MARKDOWN`). |
| `get_ukraine_time()` | Повертає поточний час в часовому поясі `Europe/Kyiv` у форматі `DD.MM.YYYY HH:MM`. |

---

### `utils/logger.py`
Аналітика використання та підрахунок вартості запитів до AI.

| Функція | Опис |
|---|---|
| `log_ai_usage(method, model_name, usage_data, user_id)` | Асинхронно записує статистику кожного запиту у **два формати**: `bot_usage.log` (текст для адміна) та `usage_analytics.jsonl` (JSON Lines для машинного аналізу). Автоматично розраховує вартість у $ за поточними тарифами OpenAI, Together та Perplexity. |

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