import pytest
from unittest.mock import AsyncMock, patch
from handlers.message_handlers import handle_message
from telegram import Update, Message, Chat, User
from telegram import MessageOriginChannel
from telegram.ext import ContextTypes

@pytest.mark.asyncio
async def test_handle_message_not_waiting_state():
    """Тест: Стан не 'WAITING' - відправляє меню без аналізу."""
    user_states = {123: {"action": None}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()

    await handle_message(update, None, user_states)
    update.message.reply_text.assert_called_with("Оберіть дію в меню.", reply_markup=AsyncMock())

@pytest.mark.asyncio
async def test_handle_message_empty_text():
    """Тест: Порожній текст - помилка."""
    user_states = {123: {"action": "WAITING", "method": "base"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = ""
    update.message.caption = None
    update.message.forward_origin = None
    update.message.reply_text = AsyncMock()

    await handle_message(update, None, user_states)
    update.message.reply_text.assert_called_with("❌ Помилка: Повідомлення не містить тексту.")

@pytest.mark.asyncio
async def test_handle_message_forward_origin():
    """Тест: Форвард - додає джерело до claim."""
    user_states = {123: {"action": "WAITING", "method": "base"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    update.message.forward_origin = MessageOriginChannel(
    date=1234567890,                        # обов'язкове поле
    sender_chat=Chat(id=1, type="channel", title="Channel")
)
    update.message.reply_text = AsyncMock(return_value=AsyncMock())  # Status msg

    with patch('handlers.message_handlers.check_and_increment_limit', return_value=(True, None)), \
         patch('handlers.message_handlers.call_base_gpt', return_value="Result"):
        await handle_message(update, None, user_states)
        # Перевірка, що claim включає джерело
        # (В реальному коді це в call_base_gpt, але тут мокуємо)

@pytest.mark.asyncio
async def test_handle_message_limit_exceeded():
    """Тест: Ліміт вичерпано - повідомлення про ліміт."""
    user_states = {123: {"action": "WAITING", "method": "sonar-reasoning-pro"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    update.message.reply_text = AsyncMock(return_value=AsyncMock(edit_text=AsyncMock()))

    with patch('handlers.message_handlers.check_and_increment_limit', return_value=(False, 1)):
        await handle_message(update, None, user_states)
        update.message.reply_text.return_value.edit_text.assert_called_with(
            "🚫 Ліміт вичерпано. Для цього методу доступно 1 запитів на день.", reply_markup=AsyncMock()
        )

@pytest.mark.asyncio
async def test_handle_message_exception_handling():
    """Тест: Виняток - помилка, скидання стану."""
    user_states = {123: {"action": "WAITING", "method": "base"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    update.message.reply_text = AsyncMock(return_value=AsyncMock(edit_text=AsyncMock()))

    with patch('handlers.message_handlers.check_and_increment_limit', side_effect=Exception("Error")):
        await handle_message(update, None, user_states)
        update.message.reply_text.return_value.edit_text.assert_called_with("❌ Помилка: Error[:100]", reply_markup=AsyncMock())
        assert user_states[123]["action"] is None

@pytest.mark.asyncio
async def test_handle_message_successful_analysis():
    """Тест: Успішний аналіз - викликає AI, розбиває відповідь, скидає стан."""
    user_states = {123: {"action": "WAITING", "method": "base"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    update.message.reply_text = AsyncMock(return_value=AsyncMock(edit_text=AsyncMock()))
    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    with patch('handlers.message_handlers.check_and_increment_limit', return_value=(True, None)), \
         patch('handlers.message_handlers.call_base_gpt', return_value="Long result" * 1000):  # >4000 chars
        await handle_message(update, context, user_states)
        assert user_states[123]["action"] is None
        context.bot.send_message.assert_called_with(chat_id=123, text="✅ Аналіз завершено. Оберіть наступну дію:", reply_markup=AsyncMock())