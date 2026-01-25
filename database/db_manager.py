import aiosqlite
import logging
from datetime import datetime

# Глобальна змінна, яка триматиме з'єднання відкритим
_db_conn: aiosqlite.Connection = None

LIMITS = {
    "sonar": 999999, 
    "sonar-reasoning-pro": 1,
    "sonar-deep-research": 0,
}

async def init_db():
    """Відкриває з'єднання і тримає його активним"""
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
        logging.info("✅ База даних підключена (Persistent Connection)")

async def close_db():
    """Коректно закриває з'єднання при вимиканні бота"""
    global _db_conn
    if _db_conn:
        await _db_conn.close()
        _db_conn = None
        logging.info("💤 База даних відключена")

async def check_and_increment_limit(user_id, model_name, admin_id):
    # 1. Швидкі перевірки без БД
    try:
        admin_id = int(admin_id) if admin_id else 0
    except:
        admin_id = 0

    if user_id == admin_id and admin_id != 0: return True, None
    if model_name == "sonar": return True, None
    
   # 3. Перевірка БД
    if _db_conn is None:
        logging.error("❌ БД не ініціалізована!")
        print("❌ Помилка: БД не ініціалізована!")
        return False, 0

    today = datetime.now().strftime('%Y-%m-%d')
    limit_value = LIMITS.get(model_name, 1000000)

    if limit_value <= 0:
        return False, 0

    try:
        # Використовуємо _db_conn напряму
        async with _db_conn.execute(
            'SELECT count, last_reset FROM usage WHERE user_id = ? AND model_name = ?', 
            (user_id, model_name)
        ) as cursor:
            row = await cursor.fetchone()

        if row:
            count, last_reset = row
            if last_reset != today:
                # Новий день -> скидаємо
                await _db_conn.execute(
                    'UPDATE usage SET count = 1, last_reset = ? WHERE user_id = ? AND model_name = ?',
                    (today, user_id, model_name)
                )
            else:
                # Перевірка ліміту
                if count >= limit_value:
                    return False, limit_value
                # Інкремент
                await _db_conn.execute(
                    'UPDATE usage SET count = count + 1 WHERE user_id = ? AND model_name = ?',
                    (user_id, model_name)
                )
        else:
            # Новий запис
            await _db_conn.execute(
                'INSERT INTO usage (user_id, model_name, count, last_reset) VALUES (?, ?, 1, ?)',
                (user_id, model_name, today)
            )

        await _db_conn.commit()
        return True, None

    except Exception as e:
        logging.error(f"DB Error: {e}")
        return False, 0