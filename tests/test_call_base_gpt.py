# Повний остаточно виправлений tests/test_call_base_gpt.py
import pytest
from unittest.mock import patch, AsyncMock, ANY
from services.ai_service import call_base_gpt


@pytest.mark.asyncio
async def test_call_base_gpt_context_formation():
    """Тест: Формування context_text з srcs."""
    verified = ["Verified1"]
    unverified = ["Unverified1"]

    # Мок response як простий об'єкт (не AsyncMock для usage)
    mock_usage = type('Usage', (), {
        'prompt_tokens': 100,
        'completion_tokens': 50,
        'total_tokens': 150
    })

    mock_response = type('Response', (), {
        'choices': [type('Choice', (), {
            'message': type('Message', (), {'content': "Result"})
        })],
        'usage': mock_usage
    })

    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create, \
         patch('services.ai_service.log_ai_usage', new_callable=AsyncMock) as mock_log:
        mock_create.return_value = mock_response

        result = await call_base_gpt("Claim", verified, unverified, "model", 123)

        # Аргументи await (бо AsyncMock)
        messages = mock_create.await_args[1]['messages']
        user_content = messages[1]['content']
        assert "--- VERIFIED SOURCES (Trusted/Official):" in user_content
        assert "Verified1" in user_content
        assert "Unverified1" in user_content

        assert result == "Result"
        mock_log.assert_called_once()


@pytest.mark.asyncio
async def test_call_base_gpt_no_sources():
    """Тест: Без srcs - default messages."""
    mock_usage = type('Usage', (), {
        'prompt_tokens': 10,
        'completion_tokens': 5,
        'total_tokens': 15
    })

    mock_response = type('Response', (), {
        'choices': [type('Choice', (), {
            'message': type('Message', (), {'content': "Result"})
        })],
        'usage': mock_usage
    })

    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        await call_base_gpt("Claim", [], [], "model", 123)

        messages = mock_create.await_args[1]['messages']
        user_content = messages[1]['content']
        assert "No official or high-trust sources found." in user_content
        assert "No additional web mentions found." in user_content


@pytest.mark.asyncio
async def test_call_base_gpt_usage_logging():
    """Тест: Логування якщо usage в response."""
    mock_usage = type('Usage', (), {'prompt_tokens': 10})

    mock_response = type('Response', (), {
        'choices': [type('Choice', (), {
            'message': type('Message', (), {'content': "Result"})
        })],
        'usage': mock_usage
    })

    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create, \
         patch('services.ai_service.log_ai_usage', new_callable=AsyncMock) as mock_log:
        mock_create.return_value = mock_response

        await call_base_gpt("Claim", [], [], "model", 123)
        mock_log.assert_called_once_with("BASE", "model", mock_usage, 123)


@pytest.mark.asyncio
async def test_call_base_gpt_temperature_and_model():
    """Тест: Параметри виклику (temperature=0.2)."""
    mock_usage = type('Usage', (), {
        'prompt_tokens': 50,
        'completion_tokens': 30,
        'total_tokens': 80
    })

    mock_response = type('Response', (), {
        'choices': [type('Choice', (), {
            'message': type('Message', (), {'content': "Result"})
        })],
        'usage': mock_usage
    })

    with patch('services.ai_service.openai_client.chat.completions.create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response

        await call_base_gpt("Claim", [], [], "gpt-model", 123)

        call_kwargs = mock_create.await_args[1]
        assert call_kwargs['model'] == "gpt-model"
        assert call_kwargs['temperature'] == 0.2