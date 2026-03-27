import logging
import json
import aiofiles
from datetime import datetime

# Налаштування звичайного текстового логу
logging.basicConfig(
    filename='bot_usage.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)

async def log_ai_usage(method, model_name, usage_data, user_id="Unknown"):
    """
    Універсальний логер для OpenAI та Perplexity з розрахунком вартості.
    """
    if not usage_data:
        logging.warning("No usage data"); 
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
    file_log = f"| ID:{user_id} | {method} | {model_name} | P:{p_tokens} C:{c_tokens} | {extra_info} | T:{total} | ${cost:.5f}"
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
    print(f" {time_str} | ID: {str(user_id):<12} | {method:10} | Cost: {color}${cost:.5f}{reset}")
    print(f" Mod: {model_name[:25]:25} | P: {p_tokens:<6} | C: {c_tokens:<6} | T: {total:<6}")
    
    # Виводимо Reasoning/Citations тільки якщо вони > 0
    details = []
    if reasoning > 0: details.append(f"Reasoning: {reasoning}")
    if citations > 0: details.append(f"Citations: {citations}")
    if queries > 0:   details.append(f"Queries: {queries}")
    
    if details:
        print(f" Details: {' | '.join(details)}")
    print("─"*75)