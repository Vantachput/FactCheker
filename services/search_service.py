import aiohttp
import json
import logging
from urllib.parse import urlparse

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


async def serper_search(query: str, api_key: str):
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
            async with session.post(url, headers=headers, json=payload, timeout=10) as response:
                
                print(f"[SERPER] Статус відповіді: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get("organic", [])
                    
                    print(f"[SERPER] Знайдено результатів: {len(results)}")
                    if len(results) > 0:
                        for i, res in enumerate(results[:3]):
                            print(f"  {i+1}. {res.get('title')} ({res.get('link')})")
                    else:
                        print("  ⚠️ ПОПЕРЕДЖЕННЯ: Google повернув порожній список organic.")
                    
                    return results
                else:
                    err_text = await response.text()
                    print(f"[SERPER] ПОМИЛКА API: {err_text}")
                    logging.error(f"Serper error status: {response.status}, text: {err_text}")
                    return []
                    
    except Exception as e:
        print(f"[SERPER] КРИТИЧНА ПОМИЛКА: {e}")
        logging.error(f"Serper error: {e}")
        return []

def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return ""

def filter_sources(results):
    verified = []
    unverified = []
    
    for r in results:
        link = r.get("link", "")
        domain = get_domain(link)

        date_info = f" [{r.get('date')}]" if r.get('date') else ""
        source_info = f"--- TITLE: {r.get('title')}\nURL: {link}{date_info}\nCONTENT: {r.get('snippet')}\n"

        is_verified = any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS)
        
        if is_verified:
            verified.append(source_info)
        else:
            unverified.append(source_info)
            
    return verified, unverified