import pytest
from datetime import datetime
import aiosqlite
from unittest.mock import patch, AsyncMock
from database.db_manager import check_and_increment_limit, LIMITS


@pytest.mark.asyncio
async def test_check_and_increment_limit_admin_bypass():
    """Тест: Адмін ігнорує ліміт."""
    allowed, limit = await check_and_increment_limit(123, "sonar-reasoning-pro", 123)
    assert allowed is True
    assert limit is None


@pytest.mark.asyncio
async def test_check_and_increment_limit_unlimited_model():
    """Тест: Безлімітна модель (sonar) завжди дозволена."""
    allowed, limit = await check_and_increment_limit(123, "sonar", 0)
    assert allowed is True
    assert limit is None


@pytest.mark.asyncio
async def test_check_and_increment_limit_new_user_new_day():
    """Тест: Новий користувач/день - створює запис, інкрементує до 1."""
    conn = await aiosqlite.connect(':memory:')
    await conn.execute('''
        CREATE TABLE usage (
            user_id INTEGER, model_name TEXT, count INTEGER, last_reset TEXT,
            PRIMARY KEY (user_id, model_name)
        )
    ''')
    await conn.commit()

    with patch('database.db_manager._db_conn', conn):
        allowed, limit = await check_and_increment_limit(123, "sonar-reasoning-pro", 0)
        assert allowed is True
        assert limit is None

        # Перевірка БД
        cursor = await conn.execute(
            'SELECT count, last_reset FROM usage WHERE user_id=123 AND model_name="sonar-reasoning-pro"'
        )
        row = await cursor.fetchone()
        assert row is not None
        assert row[0] == 1
        assert row[1] == datetime.now().strftime('%Y-%m-%d')

    await conn.close()


@pytest.mark.asyncio
async def test_check_and_increment_limit_exceed_limit():
    """Тест: Перевищення ліміту - повертає False."""
    conn = await aiosqlite.connect(':memory:')
    await conn.execute('''
        CREATE TABLE usage (
            user_id INTEGER, model_name TEXT, count INTEGER, last_reset TEXT,
            PRIMARY KEY (user_id, model_name)
        )
    ''')
    today = datetime.now().strftime('%Y-%m-%d')
    await conn.execute(
        'INSERT INTO usage (user_id, model_name, count, last_reset) VALUES (123, "sonar-reasoning-pro", 1, ?)',
        (today,)
    )
    await conn.commit()

    with patch('database.db_manager._db_conn', conn), \
         patch('database.db_manager.LIMITS', {"sonar-reasoning-pro": 1}):
        allowed, limit = await check_and_increment_limit(123, "sonar-reasoning-pro", 0)
        assert allowed is False
        assert limit == 1

        # Перевірка, що count не змінився (перевищено ліміт)
        cursor = await conn.execute(
            'SELECT count FROM usage WHERE user_id=123 AND model_name="sonar-reasoning-pro"'
        )
        row = await cursor.fetchone()
        assert row[0] == 1

    await conn.close()


@pytest.mark.asyncio
async def test_check_and_increment_limit_db_not_initialized():
    """Тест: БД не ініціалізована - повертає False."""
    with patch('database.db_manager._db_conn', None):
        allowed, limit = await check_and_increment_limit(123, "sonar-reasoning-pro", 0)
        assert allowed is False
        assert limit == 0


@pytest.mark.asyncio
async def test_check_and_increment_limit_exception_handling():
    """Тест: Виняток (e.g., SQL error) - повертає False, лог помилки."""
    conn = await aiosqlite.connect(':memory:')

    with patch('database.db_manager._db_conn', conn), \
         patch('aiosqlite.Connection.execute', side_effect=Exception("SQL error")), \
         patch('logging.error') as mock_log:
        allowed, limit = await check_and_increment_limit(123, "sonar-reasoning-pro", 0)
        assert allowed is False
        assert limit == 0
        mock_log.assert_called_with("DB Error: SQL error")

    await conn.close()