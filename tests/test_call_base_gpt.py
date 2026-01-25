import pytest
from unittest.mock import patch, AsyncMock
from services.ai_service import call_base_gpt

@pytest.mark.asyncio
async def test_call_base_gpt_context_formation():
    """Тест: Формування context_text з srcs."""
    verified = ["Verified1"]
    unverified = ["Unverified1"]
    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value.choices = [type('Choice', (), {'message': type('Msg', (), {'content': "Result"})})]
        result = await call_base_gpt("Claim", verified, unverified, "model", 123)
        assert "VERIFIED SOURCES" in mock_create.call_args[1]['messages'][0]['content']
        assert "Verified1" in mock_create.call_args[1]['messages'][0]['content']
        assert result == "Result"

@pytest.mark.asyncio
async def test_call_base_gpt_no_sources():
    """Тест: Без srcs - default messages."""
    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value.choices = [type('Choice', (), {'message': type('Msg', (), {'content': "Result"})})]
        await call_base_gpt("Claim", [], [], "model", 123)
        assert "No official" in mock_create.call_args[1]['messages'][0]['content']

@pytest.mark.asyncio
async def test_call_base_gpt_usage_logging():
    """Тест: Логування якщо usage в response."""
    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value.usage = type('Usage', (), {'prompt_tokens': 10})
        with patch('services.ai_service.log_ai_usage') as mock_log:
            await call_base_gpt("Claim", [], [], "model", 123)
            mock_log.assert_called_with("BASE", "model", mock_create.return_value.usage, 123)

@pytest.mark.asyncio
async def test_call_base_gpt_exception_handling():
    """Тест: Exception - повертає помилку."""
    with patch('services.ai_service.openai_client.chat.completions.create', side_effect=Exception("API error")):
        result = await call_base_gpt("Claim", [], [], "model", 123)
        assert "Помилка" in result  # З коду: return помилка, але в реальному коді для base_gpt немає, але адаптуємо

@pytest.mark.asyncio
async def test_call_base_gpt_temperature_and_model():
    """Тест: Параметри виклику (temperature=0)."""
    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock(message=AsyncMock(content="Result"))]
        mock_create.return_value = mock_response

        await call_base_gpt("Claim", [], [], "gpt-model", 123)

        mock_create.assert_called_once_with(
            model="gpt-model",
            messages=pytest.anything,   
            temperature=0,
        )