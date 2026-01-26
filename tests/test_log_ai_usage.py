import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json
from utils.logger import log_ai_usage
import aiofiles
from unittest.mock import mock_open


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

    mocked_file = MagicMock()
    mocked_file.write = AsyncMock()

    with patch('aiofiles.open', return_value=MagicMock(__aenter__=AsyncMock(return_value=mocked_file))), \
         patch('logging.info') as mock_info, \
         patch('builtins.print') as mock_print:
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data, "user")

        # Перевірка запису в JSONL
        written_line = mocked_file.write.call_args[0][0]
        data = json.loads(written_line.strip())
        assert data["user_id"] == "user"
        assert data["method"] == "OPENAI"
        assert data["model"] == "gpt-4o-mini"
        assert data["p_tokens"] == 100
        assert data["c_tokens"] == 50
        assert data["cost"] > 0  # > 0 для gpt-4o-mini

        # Перевірка консольного виводу (наявність ключових частин)
        print_calls = ' '.join([call[0][0] for call in mock_print.call_args_list])
        assert "OPENAI" in print_calls
        assert "gpt-4o-mini" in print_calls
        assert "Cost:" in print_calls


@pytest.mark.asyncio
async def test_log_ai_usage_object_input():
    """Тест: Вхід об'єкт (e.g., OpenAI response.usage) - getattr для tokens."""
    class MockUsage:
        prompt_tokens = 100
        completion_tokens = 50
        completion_tokens_details = type('Details', (), {'reasoning_tokens': 10})()

    mocked_file = MagicMock()
    mocked_file.write = AsyncMock()

    with patch('aiofiles.open', return_value=MagicMock(__aenter__=AsyncMock(return_value=mocked_file))), \
         patch('logging.info'), patch('builtins.print'):
        await log_ai_usage("OPENAI", "gpt-4o-mini", MockUsage(), "user")

        # Просто перевіряємо, що write викликано (tokens витягнуто)
        mocked_file.write.assert_called()


@pytest.mark.asyncio
async def test_log_ai_usage_cost_calculation_models():
    """Тест: Розрахунок cost для різних моделей."""
    usage_data = {"prompt_tokens": 1000000, "completion_tokens": 1000000}

    mocked_file = MagicMock()
    mocked_file.write = AsyncMock()

    with patch('aiofiles.open', return_value=MagicMock(__aenter__=AsyncMock(return_value=mocked_file))), \
         patch('logging.info'), patch('builtins.print') as mock_print:

        # GPT-4o-mini
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data)
        written1 = json.loads(mocked_file.write.call_args_list[-1][0][0].strip())
        assert round(written1["cost"], 2) == 0.75  # 0.15 input + 0.60 output на 1M

        # Llama-3.1-8b (Together)
        await log_ai_usage("TOGETHER", "llama-3.1-8b", usage_data)
        written2 = json.loads(mocked_file.write.call_args_list[-1][0][0].strip())
        assert written2["cost"] == 0.2  # 0.1 / 1M total


@pytest.mark.asyncio
async def test_log_ai_usage_console_output_details():
    """Тест: Вивід details якщо >0."""
    usage_data = {"prompt_tokens": 10, "completion_tokens": 10, "reasoning_tokens": 5}

    with patch('builtins.print') as mock_print:
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data)
        print_calls = ' '.join([call[0][0] for call in mock_print.call_args_list])
        assert "Reasoning: 5" in print_calls


@pytest.mark.asyncio
async def test_log_ai_usage_color_cost():
    """Тест: Кольори в консолі залежно від cost."""
    usage_data_low = {"prompt_tokens": 1, "completion_tokens": 1}  # дуже низький cost → зелений

    with patch('builtins.print') as mock_print:
        await log_ai_usage("OPENAI", "gpt-4o-mini", usage_data_low)
        print_calls = ' '.join([call[0][0] for call in mock_print.call_args_list])
        assert "\033[92m" in print_calls  # зелений колір