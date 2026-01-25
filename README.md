# AI Fact-Checker Telegram Bot
Інтелектуальна система для виявлення дезінформації в соціальних мережах за допомогою AI. Бот перевіряє новини на правдивість, використовуючи гібридну архітектуру: web-пошук (Serper + GPT), Perplexity AI з різними режимами, fine-tuned моделі (Llama 3.1, GPT-4o-mini). Користувач обирає метод через меню.

## Встановлення
1. Клонуйте репо: `git clone <url>`
2. Встановіть залежності: `pip install -r requirements.txt`
3. Створіть .env з ключами (BOT_TOKEN, OPENAI_API_KEY тощо).
4. Запустіть: `python main.py`

## Залежності (requirements.txt)
- python-telegram-bot
- aiosqlite
- aiohttp
- openai
- together
- python-dotenv
- pytz

## Структура проекту
- **db_manager.py**: Керування БД для лімітів використання (init_db, close_db, check_and_increment_limit).
- **main.py**: Головний файл запуску бота, ініціалізація, shutdown.
- **message_handlers.py**: Обробка вхідних повідомлень, виклик AI, розбиття відповідей.
- **ai_service.py**: Виклики AI-сервісів (OpenAI, Together, Perplexity), генерація пошукових запитів.
- **helpers.py**: Допоміжні функції (split_text, get_progress_bar, escape_markdown, get_ukraine_time).
- **keyboards.py**: Inline-клавіатури для Telegram-меню.
- **callback_handlers.py**: Обробка callback-запитів від кнопок, оновлення стану користувача.
- **search_service.py**: Пошуковий сервіс (Serper API), фільтрація джерел за довірою.
- **command_handlers.py**: Обробка команд (/start).
- **logger.py**: Логування AI-використання з розрахунком вартості.