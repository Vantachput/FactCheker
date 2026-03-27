"""Ядро системи штучного інтелекту: взаємодія з LLM провайдерами.

**Архітектурне рішення:**
Модуль абстрагує роботу з трьома різними AI-провайдерами:
1. OpenAI (для генерації пошукових запитів та аналізу через базові моделі).
2. Together AI (для швидкого запуску fine-tuned Llama/Містраль моделей).
3. Perplexity API (для інтерактивного ріал-тайм пошуку та deep research).

**Бізнес-логіка (Промптинг та конвеєр):**
- Функція `generate_search_query` перетворює емоційний запит користувача на
  фактичний пошуковий запит (наприклад 'Зеленський заборонив дихати' -> 'Зеленський наказ заборона').
- Базові GPT моделі (`call_base_gpt`) отримують у контекст уже відфільтровані 
  джерела (`verified` vs `unverified`), що змушує AI спиратися лише на надійні дані
  (RAG - Retrieval-Augmented Generation).
- Моделі сімейства `sonar` (Perplexity) використовують власні інструменти пошуку.
  Для них налаштовано жорсткі системні промпти, щоб унеможливити використання 
  англійської мови та змусити ІХ дотримуватися журналістських стандартів.
"""
import os

import aiohttp
from openai import AsyncOpenAI
from together import AsyncTogether

from utils.helpers import get_ukraine_time
from utils.logger import log_ai_usage

today = get_ukraine_time()
_ai_session = None
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
together_client = AsyncTogether(api_key=os.getenv("TOGETHER_API_KEY"))
print(today)

async def generate_search_query(user_text: str, model_id: str = "gpt-4o-mini") -> str:
    """Генерує оптимізований пошуковий запит з тексту користувача.
    
    Алгоритм "Search Query Architect" видаляє емоційні забарвлення, прикметники
    та конкретні (потенційно фейкові) деталі, залишаючи лише "якірні факти" 
    (Anchor Facts: дати, локації, власні назви).

    Args:
        user_text (str): Оригінальне повідомлення від користувача.
        model_id (str, optional): Модель для генерації. За замовчуванням "gpt-4o-mini".

    Returns:
        str: Короткий пошуковий запит (4-7 слів українською мовою). Якщо виникне 
            помилка, повертає перші 100 символів оригінального тексту.
    """
    sys_prompt = (
        "You are a Search Query Architect. Your goal is to find the REAL event "
        "behind a potentially distorted user claim.\n"
        "To do this, you must strip away adjectives, emotions, and specific "
        "objects that might be fake, keeping only the 'Anchor Facts'.\n\n"
        
        "ALGORITHM:\n"
        "1. Identify ANCHORS (Keep these): Dates, Locations, Proper Names "
        "(People, Organizations), Source Names (e.g., 'BBC', 'Glagola').\n"
        "2. Identify VARIABLES (Generalize these): \n"
        "   - Instead of specific numbers (e.g., '30000 uah'), use 'payment' "
        "or 'money'.\n"
        "   - Instead of specific vehicles (e.g., 'F-16', 'tank'), use "
        "'transport' or 'accident'.\n"
        "   - Instead of specific crime details, use general terms like "
        "'scandal' or 'crime'.\n"
        "3. Construct a query of 4-7 keywords.\n\n"
        
        "EXAMPLES:\n"
        "User: 'Zelensky signed order #555 to ban men from breathing'\n"
        "Query: Zelensky order ban men (We removed the specific fake number "
        "#555)\n\n"
        "User: 'In Kyiv, a T-72 tank exploded near McDonald's'\n"
        "Query: Kyiv explosion McDonald's (We removed 'T-72 tank' as it might "
        "be a car)\n\n"
        
        "OUTPUT: Single search query in the target language (Ukrainian)."
    )
    
    try:
        response = await openai_client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_text[:1000]}
            ],
            temperature=0.1
        )
        query = response.choices[0].message.content.strip()
        return query
    except Exception:
        return user_text[:100]

async def get_ai_session() -> aiohttp.ClientSession:
    """Повертає або створює глобальну aiohttp сесію для AI-запитів.
    
    Returns:
        aiohttp.ClientSession: Активна сесія для виконання HTTP-запитів.
    """
    global _ai_session
    if _ai_session is None or _ai_session.closed:
        _ai_session = aiohttp.ClientSession()
    return _ai_session

async def call_together(claim: str, model_id: str, uid: int) -> str:
    """Надсилає запит до Together AI (зазвичай для локально натренованих моделей).
    
    Args:
        claim (str): Текст повідомлення/новини для перевірки.
        model_id (str): ID моделі на платформі Together.
        uid (int): ID користувача для логування використання.

    Returns:
        str: Відповідь моделі (вердикт та аналіз).
    """

    response = await together_client.chat.completions.create(
        model=model_id, 
        messages=[
            {
                "role": "system", 
                "content": "Ти аналітик новин. Визнач, чи є надана новина "
                           "правдивою чи фейковою."
            }, 
            {"role": "user", "content": f"Текст новини: : {claim}"}
        ],
        temperature=0.1 
    )

    # ДОДАЄМО ЛОГУВАННЯ
    if hasattr(response, 'usage'):
        await log_ai_usage("TOGETHER", model_id, response.usage, uid)
    
    return response.choices[0].message.content

async def call_openai_ft(claim: str, model_id: str, user_id: int) -> str:
    """Надсилає запит до Fine-Tuned (додатково натренованої) моделі OpenAI.
    
    Args:
        claim (str): Текст новин для перевірки.
        model_id (str): ID fine-Tuned моделі (наприклад `ft:gpt-4o-mini...`).
        user_id (int): ID користувача для логування витрат.

    Returns:
        str: Повернутий моделлю вердикт.
    """
    sys_instr = (
        "Ти професійний аналітик новин. Оціни ймовірність правдивості новини у "
        "відсотках (0-100%) та надай коротке обґрунтування вердикту."
    )
    response = await openai_client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": sys_instr}, 
            {"role": "user", "content": f"Текст новини: {claim}"}
        ],
        temperature=0
    )

    if hasattr(response, 'usage'):
        await log_ai_usage("OPENAI_FT", model_id, response.usage, user_id)

    return response.choices[0].message.content

async def call_base_gpt(claim: str, verified_srcs: list[str], unverified_srcs: list[str], model_id: str, user_id: int) -> str:
    """Аналізує новину за допомогою базових моделей OpenAI із наданням контексту (RAG).
    
    Реалізує логіку:
    1. Передає масиви "Довірених" і "Неперевірених" джерел.
    2. Змушує AI порівнювати факти та шукати консенсус між джерелами.
    3. Визначає підсумковий вердикт (ПРАВДА, МАНІПУЛЯЦІЯ, ФЕЙК, НЕПІДТВЕРДЖЕНО) 
       на основі матриці логіки (Logic Matrix).

    Args:
        claim (str): Твердження користувача.
        verified_srcs (list[str]): Рядки з офіційних та перевірених сайтів (A+, A, B списки).
        unverified_srcs (list[str]): Інші джерела з Інтернету.
        model_id (str): Обрана базова модель OpenAI (наприклад `gpt-4o`).
        user_id (int): ID користувача для статистики.

    Returns:
        str: Детальний аналіз та вердикт в Markdown форматі.
    """
    # Складаємо контекст із двох рівнів довіри
    context_text = "--- VERIFIED SOURCES (Trusted/Official):\n"
    if verified_srcs:
        context_text += "\n".join(verified_srcs)
    else:
        context_text += "No official or high-trust sources found.\n"
    
    context_text += "\n--- GENERAL WEB SOURCES (Unverified/Contextual):\n"
    if unverified_srcs:
        context_text += "\n".join(unverified_srcs)
    else:
        context_text += "No additional web mentions found."

    sys_instr = (
        "ROLE: You are an elite Ukrainian Fact-Checker Bot.\n"
        f"CURRENT DATE: {today}.\n\n"
        
        "INPUT DATA:\n"
        "1. User Claim: The statement you need to verify.\n"
        "2. Search Context: Snippets from Google Search results "
        "(split into Trusted vs General).\n\n"
        
        "METHODOLOGY:\n"
        "- Analyze the snippets carefully. Even short snippets often contain "
        "the verdict (e.g., 'Fake news', 'Debunked', or official statements).\n"
        "- Prioritize 'Trusted Sources'. If Ukrinform or BBC says X, and a "
        "random blog says Y, trust X.\n"
        "- Look for consensus. If 5 sources say the same thing, it's likely "
        "true.\n"
        "- If trusted sources mention the claim is a 'fake' or 'IPSO' "
        "(propaganda), label it as [ФЕЙК].\n\n"
        
        "LOGIC MATRIX (Apply strict priority):\n"
        "1. FULL MATCH -> [ПРАВДА] (Dates, Names, Details match).\n"
        "2. PARTIAL MATCH -> [МАНІПУЛЯЦІЯ] (The core event happened at this "
        "place/time, BUT details are distorted. E.g., User says 'Tank', News "
        "says 'Car'. User says 'Died', News says 'Injured').\n"
        "3. NO EVENT -> [ФЕЙК] (No mentions of such event at this location/date "
        "found in trusted sources, or sources explicitly debunk it).\n"
        "4. NO DATA -> [НЕПІДТВЕРДЖЕНО] (Search yielded zero relevant results).\n\n"
        
        "RESPONSE FORMAT (Strict Markdown):\n"
        "**Вердикт:** [Category]\n\n"
        "**Аналіз:**\n"
        "(Short explanation citing specific sources from the context. Do not "
        "invent links. "
        "Refer to sources by name, e.g., 'За даними Укрінформ...')."

        "RESPONSE STRUCTURE:\n"
        "- Start with the most reliable source link to enable Telegram Preview. "
        "Format: [🔗 Джерело] (URL)\n"
        "- Then add two new lines.\n"
        "- Then provide the [VERDICT] and analysis.\n"
    )
    
    print(context_text)

    # Налаштування для звичайних моделей
    kwargs = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": sys_instr},
            {
                "role": "user", 
                "content": f"Claim to verify: {claim}\n\nContext Data:\n{context_text}"
            }
        ]
    }

    # Вимикаємо температуру для моделей, які її не підтримують
    if not any(x in model_id.lower() for x in ["gpt-5", "o1", "o3", "search-preview"]):
        kwargs["temperature"] = 0.2

    # 1. Отримуємо повну відповідь
    try:
        response = await openai_client.chat.completions.create(**kwargs)
    except Exception as e:
        return f"Помилка: {str(e)}"

    if hasattr(response, 'usage'):
        await log_ai_usage("BASE", model_id, response.usage, user_id)
        
    return response.choices[0].message.content

async def call_perplexity(claim: str, method: str, api_key: str, user_id: int) -> str:
    """Викликає моделі серії Sonar (Perplexity) напряму через REST API.
    
    В залежності від `method` (deep-research, reasoning-pro, sonar-huge), 
    настроює різні системні промпти, температуру, тайм-аути та ліміти токенів.
    Цей сервіс має власний пошуковий рушій, тому йому не потрібен пошук Serper.

    Args:
        claim (str): Текст для перевірки.
        method (str): Внутрішня назва моделі (наприклад `sonar-deep-research`).
        api_key (str): Ключ доступу до сервісу.
        user_id (int): ID користувача для логування витрат.

    Returns:
        str: Згенерована відповідь з оцінкою правдивості твердження.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    if method == "sonar-deep-research":
        temp = 0.3 
        freq_pen = 0.5
        sys_instr = (
            "ROLE: Senior Fact-Checking Detective.\n"
            "LANGUAGE: You MUST process information in any language but output "
            "ONLY in UKRAINIAN.\n"
            f"SYSTEM CONTEXT: The current local time in Ukraine is {today}.\n"
            "All time-sensitive analysis MUST be based on THIS date.\n"
            "Do not use any other internal system dates.\n\n"
            "Strictly ignore the language of the search results and write "
            "exclusively in Ukrainian.\n\n"
            
            "LINGUISTIC INSTRUCTIONS:\n"
            "- Use natural, high-quality Ukrainian (literary style).\n"
            "- Avoid English-style sentence structures. Adapt the meaning, "
            "don't just translate word-for-word.\n"
            "- Use active voice where possible and proper Ukrainian "
            "terminology.\n"
            "- Ensure all terms are correctly declined (proper grammatical "
            "cases).\n\n"
            
            "RESPONSE STRUCTURE:\n"
            "1. VERDICT: Start with one of these: ✅ ПРАВДА, ❌ ФЕЙК, "
            "⚠️ МАНІПУЛЯЦІЯ, or 🔍 НЕМОЖЛИВО ВСТАНОВИТИ.\n"
            "2. ADDRESSING: Write exactly: 'Ми провели глибокий аналіз, і ось "
            "що вдалося знайти...'.\n"
            "3. BODY: Use these three sections with emojis:\n"
            "   - 📌 Контекст (The background of the claim)\n"
            "   - 🛡️ Докази (Evidence gathered)\n"
            "   - 🏁 Висновок (Final summary)\n\n"
            
            "STRICT CONSTRAINTS:\n"
            "- NO ENGLISH: Not a single word in English in the final response.\n"
            "- NO CITATIONS: Absolutely NO links, URLS, or bracketed numbers "
            "like [1], [2], [3].\n"
            "- CONCISENESS: Be brief and professional. Avoid long-winded "
            "essays.\n"
            "- LENGTH: Total response must be under 5000 characters."
        )
        current_timeout = 300

    elif method == "sonar-reasoning-pro":
        temp = 0.1 
        freq_pen = 0.1
        sys_instr = (
            f"SYSTEM CONTEXT:\n"
            f"The current local time in Ukraine is {today}. "
            f"All time-sensitive analysis MUST be based strictly on this date. "

            "ROLE:\n"
            "You are an expert fact-checking analyst specializing in logical "
            "analysis, manipulation detection, and critical reasoning.\n\n"

            "LANGUAGE REQUIREMENTS:\n"
            "- Output ONLY in high-quality, formal Ukrainian.\n"
            "- Use natural Ukrainian syntax and professional journalistic style.\n"
            "- Avoid calques or English-style phrasing.\n\n"

            "SEARCH & EVIDENCE REQUIREMENTS:\n"
            "- Perform a real-time search to verify the claim against current "
            "facts.\n"
            "- Prioritize credible Ukrainian sources, specifically official .ua "
            "domains, Suspilne, Ukrinform, BBC News Ukraine, and specialized "
            "fact-checking projects like StopFake.\n"
            "- For every fact or piece of evidence found, provide a direct "
            "source link in parentheses.\n"
            "- If no reliable information is found online, explicitly state "
            "that the claim lacks empirical confirmation.\n\n"
            
            "RESPONSE STRUCTURE (MANDATORY):\n"
            "1. ВЕРДИКТ — start the response with exactly ONE of the following "
            "labels:\n"
            "   ✅ ПРАВДА\n"
            "   ❌ ФЕЙК\n"
            "   ⚠️ МАНІПУЛЯЦІЯ\n"
            "   🔍 НЕМОЖЛИВО ВСТАНОВИТИ\n\n"
            "2. АНАЛІЗ — a concise, logically structured explanation that:\n"
            "- explicitly refers to the internal logic of the claim;\n"
            "- identifies specific logical fallacies or manipulation "
            "techniques (if present);\n"
            "- avoids speculation or assumptions beyond the given text.\n\n"

            "STRICT CONSTRAINTS:\n"
            "- DO NOT cite sources, links, footnotes, or external references.\n"
            "- DO NOT introduce new factual information that is not present in "
            "the claim.\n"
            "- DO NOT soften conclusions with uncertainty phrases unless the "
            "verdict is 🔍 НЕМОЖЛИВО ВСТАНОВИТИ.\n"
            "- Maintain an analytical, neutral, and professional tone.\n"
        )
        current_timeout = 180

    else: 
        temp = 0.6 
        freq_pen = 0.4
        sys_instr = (
            f"SYSTEM CONTEXT: Current date: {today} (Kyiv time). Use this for "
            "all timeliness checks.\n\n"
            
            "ROLE: You are an elite Ukrainian Investigative Journalist and "
            "Fact-Checker.\n"
            "Your goal is to verify the ESSENCE of the event, not just the "
            "exact wording of the user's claim.\n\n"
            
            "SEARCH STRATEGY (INTERNAL):\n"
            "1. Extract key entities (names, places, dates) from the user's "
            "claim.\n"
            "2. Search for these specific events in reputable media.\n"
            "3. If the user's wording is emotional but the event happened -> "
            "Verdict: TRUE or MANIPULATION.\n"
            "4. Only use FAKE if the event did not happen at all or is a "
            "complete fabrication.\n\n"

            "OUTPUT FORMAT (STRICTLY UKRAINIAN):\n"
            "1. VERDICT: Choose one: [✅ ПРАВДА], [❌ ФЕЙК], [⚠️ МАНІПУЛЯЦІЯ], "
            "[🔍 НЕМОЖЛИВО ВСТАНОВИТИ].\n"
            "2. EXPLANATION: A cohesive, flowing narrative explanation (2-3 "
            "paragraphs).\n"
            "   - Describe what actually happened according to official "
            "sources.\n"
            "   - Compare it with the user's claim.\n"
            "   - Mention specific dates and names found during the search.\n\n"

            "CRITICAL CONSTRAINTS:\n"
            "- NO CITATION TAGS: Do not include [1], [2], (1) or any source "
            "indexes. The text must be clean.\n"
            "- NO LINKS: Do not output URLs.\n"
            "- TONE: Professional, objective, journalistic Ukrainian. Avoid "
            "translationese.\n"
            "- Do NOT simply say 'no information found' immediately. Try "
            "different search angles first."
        )
        current_timeout = 120

    payload = {
        "model": method, 
        "messages": [
            {"role": "system", "content": sys_instr}, 
            {"role": "user", "content": claim}
        ],
        "max_tokens": 3000 if "deep" in method else 1500,
        "temperature": temp,
        "frequency_penalty": freq_pen
    }

    session = await get_ai_session() # Отримуємо спільну сесію

    try:
            timeout_config = aiohttp.ClientTimeout(total=current_timeout)
            async with session.post(
                "https://api.perplexity.ai/chat/completions", 
                headers=headers, 
                json=payload, 
                timeout=timeout_config
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    await log_ai_usage(
                        "PERPLEXITY", method, data.get('usage', {}), user_id
                    )
                    return data['choices'][0]['message']['content']
                else:
                    return f"❌ Помилка API: {response.status}"
    except Exception as e:
        return f"❌ Помилка з'єднання: {str(e)}"