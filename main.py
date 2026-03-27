"""Головний модуль Telegram-бота для перевірки фактів.

Цей модуль відповідає за ініціалізацію Telegram-застосунку, налаштування 
обробників повідомлень та команд, а також життєвий цикл роботи бота, 
включно з коректним завершенням (graceful shutdown).
"""
import asyncio
import os

from dotenv import load_dotenv
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from database.db_manager import close_db, init_db
from handlers.callback_handlers import handle_callback
from handlers.command_handlers import start
from handlers.message_handlers import handle_message

load_dotenv()
user_states = {}


async def start_wrapper(u, c):
    """Обгортка для обробника команди /start.

    Args:
        u (telegram.Update): Запит оновлення від Telegram.
        c (telegram.ext.ContextTypes.DEFAULT_TYPE): Контекст бота.
    """
    await start(u, c, user_states)

async def callback_wrapper(u, c):
    """Обгортка для обробника callback-запитів.

    Args:
        u (telegram.Update): Запит оновлення від Telegram.
        c (telegram.ext.ContextTypes.DEFAULT_TYPE): Контекст бота.
    """
    await handle_callback(u, c, user_states)

async def message_wrapper(u, c):
    """Обгортка для обробника текстових повідомлень.

    Args:
        u (telegram.Update): Запит оновлення від Telegram.
        c (telegram.ext.ContextTypes.DEFAULT_TYPE): Контекст бота.
    """
    await handle_message(u, c, user_states)

async def main():
    """Основна функція запуску бота та ініціалізації ресурсів.
    
    Створює підключення до бази даних, збирає ApplicationBuilder 
    від бібліотеки python-telegram-bot, реєструє обробники повідомлень 
    (routers) і запускає цикл (polling). При зупинці коректно закриває
    всі з'єднання з AI сесіям та БД.
    """

    await init_db()

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    
    app.add_handler(CommandHandler("start", start_wrapper))
    app.add_handler(CallbackQueryHandler(callback_wrapper))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_wrapper))
    
    print("🚀 Бот запущений асинхронно...")

    # 3. Запуск через контекстний менеджер (найбільш стабільний варіант)
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        try:
            # Чекаємо нескінченно, поки не натиснуть Ctrl+C
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            # Це виключення виникає при зупинці asyncio.run
            print("\n⏳ Зупинка процесів...")
        finally:
            # 1. Зупиняємо Telegram процеси
            if app.updater.running:
                await app.updater.stop()
            await app.stop()
            # Закриваємо БД
            await close_db()
            # Закриваємо AI сесію
            from services.ai_service import _ai_session
            if _ai_session:
                await _ai_session.close()
                print("✅ AI сесія закрита.")

            print("🛑 Бот повністю зупинений. Гарного дня!")

if __name__ == "__main__":
    try:
        # Одне єдине місце входу в асинхронність
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Бот зупинений користувачем.")