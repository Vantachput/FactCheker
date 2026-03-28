"""Модуль для роботи з локальною базою даних SQLite.

Цей модуль відповідає за ініціалізацію та підтримку постійного (persistent)
з'єднання з базою даних `bot_data.db`. Основне призначення БД — це ведення 
обліку використання користувачами платних моделей штучного інтелекту, 
встановлення денних лімітів та їх обнулення.
"""
import logging
from datetime import datetime

import aiosqlite

from utils.logger import logger

# Глобальна змінна, яка триматиме з'єднання відкритим
_db_conn: aiosqlite.Connection = None

LIMITS = {
    "sonar": 999999, 
    "sonar-reasoning-pro": 1,
    "sonar-deep-research": 0,
}

async def init_db():
    """Ініціалізує та відкриває постійне з'єднання з базою даних.
    
    Створює таблицю `usage`, якщо вона ще не існує. 
    Таблиця зберігає `user_id`, `model_name`, `count` (кількість запитів)
    та `last_reset` (дату останнього обнулення).
    
    Зверніть увагу, що ми не використовуємо контекстний менеджер `async with`,
    оскільки нам потрібно зберегти з'єднання відкритим у глобальній змінній 
    `_db_conn` для швидкого доступу під час обробки повідомлень.
    """
    global _db_conn
    if _db_conn is None:
        # Ми НЕ використовуємо 'async with', щоб з'єднання не закрилося
        _db_conn = await aiosqlite.connect('bot_data.db')
        
        # Створюємо таблицю, якщо її немає
        await _db_conn.execute('''
            CREATE TABLE IF NOT EXISTS usage (
                user_id INTEGER, model_name TEXT, count INTEGER, last_reset TEXT,
                PRIMARY KEY (user_id, model_name)
            )
        ''')
        await _db_conn.commit()
        logger.info("✅ База даних підключена (Persistent Connection)")

async def close_db():
    """Коректно закриває активне з'єднання з базою даних.
    
    Ця функція повинна викликатися при зупинці роботи бота.
    """
    global _db_conn
    if _db_conn:
        await _db_conn.close()
        _db_conn = None
        logger.info("💤 База даних відключена")

async def check_and_increment_limit(user_id, model_name, admin_id):
    """Перевіряє ліміти використання моделі та інкрементує лічильник.
    
    Якщо ліміт вичерпано, або виникла помилка підключення — повертає False.
    Для безкоштовних моделей (наприклад "sonar") або для адміністратора
    перевірка завжди успішна і лічильник не збільшується.
    Ліміти автоматично оновлюються (скидаються) на початку нової доби.

    Args:
        user_id (int): ID користувача Telegram.
        model_name (str): Назва моделі (наприклад `sonar-reasoning-pro`).
        admin_id (int | str): ID адміністратора бота (перевіряється на співпадіння з user_id).

    Returns:
        tuple[bool, int | None]: Кортеж з двох значень:
            - bool: True, якщо запит дозволено, False — якщо ліміт вичерпано.
            - int | None: Залишок або денний ліміт. Для успішних або безлімітних запитів зазвичай None.
    """
    # 1. Швидкі перевірки без БД
    try:
        admin_id = int(admin_id) if admin_id else 0
    except (ValueError, TypeError):
        admin_id = 0

    if user_id == admin_id and admin_id != 0:
        return True, None
    if model_name == "sonar":
        return True, None
    
   # 3. Перевірка БД
    if _db_conn is None:
        logger.error("❌ Помилка: БД не ініціалізована!")
        return False, 0

    today = datetime.now().strftime('%Y-%m-%d')
    limit_value = LIMITS.get(model_name, 1000000)

    if limit_value <= 0:
        return False, 0

    try:
        # Використовуємо _db_conn напряму
        async with _db_conn.execute(
            'SELECT count, last_reset FROM usage '
            'WHERE user_id = ? AND model_name = ?', 
            (user_id, model_name)
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            count, last_reset = row
            if last_reset != today:
                # Новий день -> скидаємо
                await _db_conn.execute(
                    'UPDATE usage SET count = 1, last_reset = ? '
                    'WHERE user_id = ? AND model_name = ?',
                    (today, user_id, model_name)
                )
            else:
                # Перевірка ліміту
                if count >= limit_value:
                    return False, limit_value
                # Інкремент
                await _db_conn.execute(
                    'UPDATE usage SET count = count + 1 '
                    'WHERE user_id = ? AND model_name = ?',
                    (user_id, model_name)
                )
        else:
            # Новий запис
            await _db_conn.execute(
                'INSERT INTO usage (user_id, model_name, count, last_reset) '
                'VALUES (?, ?, 1, ?)',
                (user_id, model_name, today)
            )

        await _db_conn.commit()
        return True, None

    except Exception as e:
        logger.error(f"DB Error: {e}", exc_info=True)
        return False, 0