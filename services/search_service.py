"""Сервіс пошуку через Serper API з фільтрацією джерел.

**Архітектурне рішення:**
Цей модуль відділяє логіку веб-пошуку від роботи з ШІ. Ми використовуємо Serper.dev 
як проксі для Google Search API. Основна фішка модуля — це механізм `filter_sources`, 
який реалізує *бізнес-логіку перевірки надійності*.

**Бізнес-логіка (Алгоритм фільтрації джерел):**
1. Отримані від Google результати перевіряються по URL.
2. Парсер витягує доменне ім'я з URL.
3. Домен порівнюється з `ALLOWED_DOMAINS` — жорстко заданим списком "білих" 
   ресурсів (офіційні урядові сайти, світові медіа рівня A+, A, B).
4. Результати розділяються на `verified` (перевірені) і `unverified` (інші), 
   що дозволяє ШІ у майбутньому посилатися лише на надійні джерела.
"""
import logging
from urllib.parse import urlparse

import aiohttp

SOURCES = {
    # Офіційні державні ресурси та реєстри
    "A_PLUS": [
        "president.gov.ua", "kmu.gov.ua", "rada.gov.ua", "mil.gov.ua", "mod.gov.ua",
        "prozorro.gov.ua", "prozorro.sale", "setam.net.ua", "rnbo.gov.ua", 
        "mfa.gov.ua", "nbu.gov.ua", "mof.gov.ua", "court.gov.ua", "diia.gov.ua",
        "gp.gov.ua", "ssu.gov.ua", "npu.gov.ua", "dbr.gov.ua", "nabu.gov.ua"
    ],
    
    # Світові агенції та надійні державні медіа України
    "A": [
        "reuters.com", "apnews.com", "bbc.com", "dw.com", "ukrinform.ua", 
        "voanews.com", "radiosvoboda.org", "bloomberg.com", "nytimes.com"
    ],
    
    # Якісні приватні медіа та профільні бізнес-видання
    "B": [
        "suspilne.media", "pravda.com.ua", "interfax.com.ua", "unian.net", 
        "lb.ua", "theguardian.com", "biz.nv.ua", "epravda.com.ua", 
        "forbes.ua", "liga.net", "tsn.ua", "rbc.ua", "ukraine-crisis.org",
        "hromadske.ua", "babel.ua", "censor.net"
    ]
}
ALLOWED_DOMAINS = SOURCES["A_PLUS"] + SOURCES["A"] + SOURCES["B"]


async def serper_search(query: str, api_key: str) -> list[dict]:
    """Виконує асинхронний пошук в Google через Serper API.
    
    Метод відправляє POST-запит з вказаним ключем та пошуковим запитом. 
    Налаштовано параметри `gl=ua` та `hl=uk` для пріоритезації 
    українського контенту.

    Args:
        query (str): Пошуковий запит (наприклад, згенерований LLM).
        api_key (str): Ключ доступу до Serper API.

    Returns:
        list[dict]: Список словників з органічними результатами пошуку.
            Кожен словник містить ключі 'title', 'link', 'snippet' тощо.
            У разі помилки повертає порожній список.
    """
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key, 
        'Content-Type': 'application/json'
    }
    
    # Створюємо чистий словник (Python dict)
    short_query = query[:150] 
    payload = {
        "q": short_query, 
        "gl": "ua", 
        "hl": "uk",
        "num": 10 
    }
    
    print(f"\n[SERPER] Надіслано запит: {short_query}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, json=payload, timeout=10
            ) as response:
                
                print(f"[SERPER] Статус відповіді: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get("organic", [])
                    
                    print(f"[SERPER] Знайдено результатів: {len(results)}")
                    if len(results) > 0:
                        for i, res in enumerate(results[:3]):
                            print(f"  {i+1}. {res.get('title')} ({res.get('link')})")
                    else:
                        print(
                            "  ⚠️ ПОПЕРЕДЖЕННЯ: Google повернув порожній "
                            "список organic."
                        )
                    
                    return results
                else:
                    err_text = await response.text()
                    print(f"[SERPER] ПОМИЛКА API: {err_text}")
                    logging.error(
                        f"Serper error status: {response.status}, text: {err_text}"
                    )
                    return []
                    
    except Exception as e:
        print(f"[SERPER] КРИТИЧНА ПОМИЛКА: {e}")
        logging.error(f"Serper error: {e}")
        return []

def get_domain(url: str) -> str:
    """Витягує чисте доменне ім'я з URL.
    
    Args:
        url (str): Повна адреса (наприклад, https://www.bbc.com/news).
        
    Returns:
        str: Домен без схеми та `www.`, наприклад `bbc.com`.
        
    Examples:
        >>> get_domain("https://www.bbc.com/news")
        'bbc.com'
    """
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""

def filter_sources(results: list[dict]) -> tuple[list[str], list[str]]:
    """Розділяє результати пошуку на надійні та ненадійні.
    
    Кожен знайдений результат порівнюється зі списком `ALLOWED_DOMAINS`.
    Результати форматуються у вигляді текстових блоків для подальшої
    передачі у промпт штучному інтелекту.

    Args:
        results (list[dict]): Список результатів від `serper_search`.

    Returns:
        tuple[list[str], list[str]]: Два списки відформатованих результатів:
            `(verified_sources, unverified_sources)`.
            
    Examples:
        >>> filter_sources([{'link':'https://bbc.com', 'title':'T', 'snippet':'S'}])
        (['--- TITLE: T\\nURL: https://bbc.com\\nCONTENT: S\\n'], [])
    """
    verified = []
    unverified = []
    
    for r in results:
        link = r.get("link", "")
        domain = get_domain(link)

        date_info = f" [{r.get('date')}]" if r.get('date') else ""
        source_info = (
            f"--- TITLE: {r.get('title')}\n"
            f"URL: {link}{date_info}\n"
            f"CONTENT: {r.get('snippet')}\n"
        )

        is_verified = any(
            domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS
        )
        
        if is_verified:
            verified.append(source_info)
        else:
            unverified.append(source_info)
            
    return verified, unverified