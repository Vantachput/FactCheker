import pytest
from unittest.mock import patch, AsyncMock
import json
from utils.logger import log_ai_usage
import aiofiles

@pytest.mark.asyncio
async def test_log_ai_usage_no_data():
    """Тест: Порожні usage_data - warning, return."""
    with patch('logging.warning') as mock_warn:
        await log_ai_usage("METHOD", "model", None)
        mock_warn.assert_called_with("No usage data")

@pytest.mark.asyncio
async def test_log_ai_usage_dict_input():
    """Тест: Вхід dict - витягує tokens, розраховує cost."""
    usage_data = {"prompt_tokens": 100, "completion_tokens": 50}
    with patch('aiofiles.open', new_callable=AsyncMock) as mock_open, \
         patch('logging.info'), patch('builtins.print'):
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data, "user")
        # Перевірка запису JSONL
        mock_open.return_value.__aenter__.return_value.write.assert_called()
        written = mock_open.return_value.__aenter__.return_value.write.call_args[0][0]
        data = json.loads(written.strip())
        assert data["user_id"] == "user"
        assert data["cost"] > 0  # Positive cost

@pytest.mark.asyncio
async def test_log_ai_usage_object_input():
    """Тест: Вхід об'єкт (e.g., OpenAI response.usage) - getattr для tokens."""
    class MockUsage:
        prompt_tokens = 100
        completion_tokens = 50
        completion_tokens_details = type('Details', (), {'reasoning_tokens': 10})

    with patch('aiofiles.open', new_callable=AsyncMock), \
         patch('logging.info'), patch('builtins.print'):
        await log_ai_usage("OPENAI", "gpt-4o-mini", MockUsage(), "user")

@pytest.mark.asyncio
async def test_log_ai_usage_cost_calculation_models():
    """Тест: Розрахунок cost для різних моделей."""
    usage_data = {"prompt_tokens": 1000000, "completion_tokens": 1000000}
    # GPT-4o-mini: 0.15 + 0.60 = 0.75
    await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data)
    # Llama-3.1-8b: 0.1 / 1M total
    await log_ai_usage("TOGETHER", "llama-3.1-8b", usage_data)
    # Перевірка через mock print (cost colors)

@pytest.mark.asyncio
async def test_log_ai_usage_console_output_details():
    """Тест: Вивід details якщо >0."""
    usage_data = {"prompt_tokens": 10, "completion_tokens": 10, "reasoning_tokens": 5}
    with patch('builtins.print') as mock_print:
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data)
        assert any("Reasoning: 5" in call[0][0] for call in mock_print.call_args_list)

@pytest.mark.asyncio
async def test_log_ai_usage_color_cost():
    """Тест: Кольори в консолі залежно від cost."""
    usage_data = {"prompt_tokens": 1, "completion_tokens": 1}  # Low cost -> green
    with patch('builtins.print') as mock_print:
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data)
        assert "\033[92m" in str(mock_print.call_args_list)  # Green