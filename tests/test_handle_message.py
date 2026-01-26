# Повний виправлений tests/test_handle_message.py (з фіксом patch та context)
import pytest
from unittest.mock import AsyncMock, patch, ANY, MagicMock
from handlers.message_handlers import handle_message
from telegram import Update, Chat
from telegram.ext import ContextTypes


@pytest.mark.asyncio
async def test_handle_message_not_waiting_state():
    user_states = {123: {"action": None}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()

    await handle_message(update, None, user_states)
    update.message.reply_text.assert_called_with("Оберіть дію в меню.", reply_markup=ANY)


@pytest.mark.asyncio
async def test_handle_message_empty_text():
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

    # Мокуємо forward_origin з потрібними атрибутами згідно реальному коду
    forward_origin = MagicMock()
    forward_origin.type = "channel"  # string, як у коді: origin.type == "channel"
    forward_origin.chat.title = "Test Channel"  # origin.chat.title
    update.message.forward_origin = forward_origin

    status_msg = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=status_msg)

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    with patch('handlers.message_handlers.check_and_increment_limit', return_value=(True, None)), \
         patch('handlers.message_handlers.generate_search_query', return_value="mock query"), \
         patch('handlers.message_handlers.serper_search', return_value=[]), \
         patch('handlers.message_handlers.filter_sources', return_value=(["verified"], ["unverified"])), \
         patch('handlers.message_handlers.call_base_gpt', return_value="Result") as mock_call_base_gpt:

        await handle_message(update, context, user_states)

    # Тепер claim точно містить джерело (бо умова origin.type == "channel" спрацьовує)
    claim_arg = mock_call_base_gpt.call_args[0][0]
    assert "Новина з джерела (Test Channel)" in claim_arg
    assert "News" in claim_arg

    # Додатково перевіряємо фінальне повідомлення
    context.bot.send_message.assert_called()


@pytest.mark.asyncio
async def test_handle_message_limit_exceeded():
    user_states = {123: {"action": "WAITING", "method": "sonar-reasoning-pro"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    status_msg = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=status_msg)

    with patch('handlers.message_handlers.check_and_increment_limit', return_value=(False, 1)):
        await handle_message(update, None, user_states)

    status_msg.edit_text.assert_called_with(
        "🚫 Ліміт вичерпано. Для цього методу доступно 1 запитів на день.",
        reply_markup=ANY
    )


@pytest.mark.asyncio
async def test_handle_message_exception_handling():
    user_states = {123: {"action": "WAITING", "method": "base"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    status_msg = AsyncMock()
    update.message.reply_text = AsyncMock(return_value=status_msg)

    with patch('handlers.message_handlers.check_and_increment_limit', side_effect=Exception("Test error")):
        await handle_message(update, None, user_states)

    status_msg.edit_text.assert_called_with(
        "❌ Помилка: Test error",
        reply_markup=ANY
    )
    assert user_states[123]["action"] is None


@pytest.mark.asyncio
async def test_handle_message_successful_analysis():
    user_states = {123: {"action": "WAITING", "method": "base"}}
    update = AsyncMock(spec=Update)
    update.effective_user.id = 123
    update.message.text = "News"
    status_msg = AsyncMock()
    update.message.reply_text = AsyncMock()

    context = AsyncMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot.send_message = AsyncMock()

    long_result = "Long result " * 1000

    with patch('handlers.message_handlers.check_and_increment_limit', return_value=(True, None)), \
         patch('handlers.message_handlers.generate_search_query', return_value="mock query"), \
         patch('handlers.message_handlers.serper_search', return_value=[]), \
         patch('handlers.message_handlers.filter_sources', return_value=(["verified"], ["unverified"])), \
         patch('handlers.message_handlers.call_base_gpt', return_value=long_result):
        await handle_message(update, context, user_states)

    assert user_states[123]["action"] is None
    context.bot.send_message.assert_called_with(
        chat_id=123,
        text="✅ Аналіз завершено. Оберіть наступну дію:",
        reply_markup=ANY
    )
    assert update.message.reply_text.call_count >= 2  # статус + частини результату