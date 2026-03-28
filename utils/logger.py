"""Система логування та аналітики витрат бота.

**Бізнес-логіка (Трекінг вартості):**
Модуль відповідає за запис усієї статистики використання AI. 
Кожен запит від користувача конвертується у кількість токенів, які
перекладаються у долари згідно з тарифами провайдерів (OpenAI, Together).
Дані зберігаються у двох форматах:
1. `bot_usage.log` - звичайний текстовий лог для швидкого читання адміном.
2. `usage_analytics.jsonl` - структурований JSON Lines файл для глибокої
   машинної аналітики чи побудови графіків.
"""
import json
import logging
from datetime import datetime

import sys

# Створюємо глобальний логер для застосунку
logger = logging.getLogger("factchecker")

def setup_logging():
    """Ініціалізація базової системи логування для всього застосунку.
    
    Встановлює формат виводу, рівні (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    та налаштовує хендлери (консоль + файл).
    """
    # Базове налаштування кореневого логера
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('app.log', encoding='utf-8')
        ]
    )
    
    # Зменшуємо рівень логування для "шумних" зовнішніх бібліотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)

    logger.info("Система логування ініціалізована.")

async def log_ai_usage(method: str, model_name: str, usage_data: object, user_id: str | int = "Unknown"):
    """Універсальний асинхронний логер для збору статистики токенів та витрат.
    
    Функція адаптується до різних форматів об'єкта `usage_data` (звичний словник 
    чи Pydantic модель від OpenAI/Together). Вона ідентифікує модель за назвою 
    та автоматично підставляє актуальні тарифи за 1 млн токенів для розрахунку 
    фінальної ціни `cost`.

    Args:
        method (str): Метод виклику (наприклад `BASE`, `PERPLEXITY`).
        model_name (str): Точна назва моделі (наприклад `gpt-4o-mini`).
        usage_data (object | dict): Об'єкт із кількістю використаних токенів.
        user_id (str | int, optional): ID користувача у Telegram.
    """
    if not usage_data:
        logging.warning("No usage data") 
        return
    # --- 1. Отримання токенів (Універсально для dict та об'єктів) ---
    if isinstance(usage_data, dict):
        p_tokens = usage_data.get('prompt_tokens', 0)
        c_tokens = usage_data.get('completion_tokens', 0)
        total = usage_data.get('total_tokens', p_tokens + c_tokens)
        reasoning = usage_data.get('reasoning_tokens', 0)
        citations = usage_data.get('citation_tokens', 0)
        queries = usage_data.get('num_search_queries', 0)
        cost = usage_data.get('cost', {}).get('total_cost', 0)
    else:
        # Для об'єктів OpenAI (наприклад, response.usage)
        p_tokens = getattr(usage_data, 'prompt_tokens', 0)
        c_tokens = getattr(usage_data, 'completion_tokens', 0)
        total = getattr(usage_data, 'total_tokens', p_tokens + c_tokens)
        details = getattr(usage_data, 'completion_tokens_details', None)
        reasoning = getattr(details, 'reasoning_tokens', 0) if details else 0
        citations = 0
        queries = 0
        cost = 0

    model_lower = model_name.lower()

    # 1. Розрахунок для OpenAI Fine-tuning
    if "ft:gpt-4o-mini" in model_lower:
        # Приблизні тарифи: $3.00 / 1M input, $12.00 / 1M output
        cost = (p_tokens * 3.0 / 1_000_000) + (c_tokens * 12.0 / 1_000_000)
    
    # 2. Розрахунок для Together AI (Llama 3.1 8B/70B)
    elif "llama-3.1-8b" in model_lower:
        cost = (p_tokens + c_tokens) * 0.1 / 1_000_000
    elif "llama-3.1-70b" in model_lower:
        cost = (p_tokens + c_tokens) * 0.8 / 1_000_000

    # 3. Стандартний GPT-4o-mini
    elif "gpt-4o-mini" in model_lower:
        cost = (p_tokens * 0.15 / 1_000_000) + (c_tokens * 0.60 / 1_000_000)
        # 4. GPT-5-mini
    
    elif "gpt-5-mini" in model_lower:
        # Тарифи: $0.25 за 1M вхідних, $2.00 за 1M вихідних токенів
        cost = (p_tokens * 0.25 / 1_000_000) + (c_tokens * 2.00 / 1_000_000)

    # --- 3. Збереження в JSONL (Аналітика) ---
    analytics_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "method": method,
        "model": model_name,
        "p_tokens": p_tokens,
        "c_tokens": c_tokens,
        "reasoning": reasoning,
        "cost": round(cost, 6)
    }
    # Використовуємо aiofiles для неблокуючого запису
    async with aiofiles.open('usage_analytics.jsonl', mode='a', encoding='utf-8') as f:
        await f.write(json.dumps(analytics_entry) + '\n')

    # --- 4. Формування запису для текстового файлу ---
    extra_info = f"R:{reasoning}, Cit:{citations}, Q:{queries}"
    file_log = (
        f"| ID:{user_id} | {method} | {model_name} | P:{p_tokens} "
        f"C:{c_tokens} | {extra_info} | T:{total} | ${cost:.5f}"
    )
    logging.info(file_log)

    # --- 5. Гарний вивід у консоль ---
    time_str = datetime.now().strftime('%H:%M:%S')
    
    # Кольори для вартості запиту
    if cost < 0.005:
        color = "\033[92m" # Зелений (дешево)
    elif cost < 0.05:
        color = "\033[93m" # Жовтий (середньо)
    else:
        color = "\033[91m" # Червоний (дорого / Deep Research)
    reset = "\033[0m"

    print("\n" + "─"*75)
    print(
        f" {time_str} | ID: {str(user_id):<12} | {method:10} | "
        f"Cost: {color}${cost:.5f}{reset}"
    )
    print(
        f" Mod: {model_name[:25]:25} | P: {p_tokens:<6} | C: {c_tokens:<6} | "
        f"T: {total:<6}"
    )
    
    # Виводимо Reasoning/Citations тільки якщо вони > 0
    details = []
    if reasoning > 0:
        details.append(f"Reasoning: {reasoning}")
    if citations > 0:
        details.append(f"Citations: {citations}")
    if queries > 0:
        details.append(f"Queries: {queries}")
    
    if details:
        print(f" Details: {' | '.join(details)}")
    print("─"*75)