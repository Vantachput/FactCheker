"""Тестові сценарії для вимірювання продуктивності FactChecker.

Кожен сценарій ізольований та не вимагає підключення до реальних зовнішніх API.
Для БД використовується тимчасова in-memory SQLite базa.

Сценарії:
    - scenario_db_stress: 100 ітерацій check_and_increment_limit.
    - scenario_memory_baseline: Baseline пам'яті без AI, тільки БД.
    - scenario_cpu_query_generation: CPU-профіль функції генерації пошукового запиту (mock).
    - scenario_full_pipeline: Повний pipeline (mock AI відповідь + DB + фільтр джерел).
"""
import asyncio
import time

import aiosqlite

from profiling.cpu_profiler import profile_cpu_async
from profiling.db_profiler import DBProfiler
from profiling.memory_profiler import MemorySnapshot


# ---------------------------------------------------------------------------
# Допоміжні функції для сценаріїв (без реальних API-викликів)
# ---------------------------------------------------------------------------

async def _create_test_db() -> aiosqlite.Connection:
    """Створює in-memory SQLite БД зі схемою, ідентичною бойовій.

    Returns:
        aiosqlite.Connection: Відкрите з'єднання з тестовою БД.
    """
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            user_id INTEGER,
            model_name TEXT,
            count INTEGER,
            last_reset TEXT,
            PRIMARY KEY (user_id, model_name)
        )
    """)
    await conn.commit()
    return conn


def _mock_filter_sources(sources: list[dict]) -> tuple[list[str], list[str]]:
    """Mock-версія filter_sources: розподіляє джерела за рівнем довіри.

    Args:
        sources: Список словників з ключами 'link' та 'snippet'.

    Returns:
        tuple[list[str], list[str]]: (verified_sources, unverified_sources)
    """
    trusted_domains = {"ukrinform.ua", "suspilne.media", "bbc.com", "pravda.com.ua"}
    verified, unverified = [], []
    for src in sources:
        domain = src.get("link", "").split("/")[2] if "://" in src.get("link", "") else ""
        text = f"[{domain}] {src.get('snippet', '')}"
        if any(td in domain for td in trusted_domains):
            verified.append(text)
        else:
            unverified.append(text)
    return verified, unverified


# ---------------------------------------------------------------------------
# Сценарій 1: Стрес-тест бази даних
# ---------------------------------------------------------------------------

async def scenario_db_stress(iterations: int = 100) -> dict:
    """Стрес-тест: 100 ітерацій INSERT/SELECT/UPDATE до таблиці usage.

    Вимірює:
        - Час окремих DB-запитів (ms)
        - Загальний час сценарію
        - Пікову пам'ять під час операцій

    Args:
        iterations: Кількість ітерацій (за замовчуванням 100).

    Returns:
        dict: Словник з метриками {'total_ms', 'avg_ms', 'peak_kb'}.
    """
    print(f"\n{'#'*60}")
    print(f"# SCENARIO 1: DB Stress Test ({iterations} iterations)")
    print(f"{'#'*60}")
    conn = await _create_test_db()
    db_prof = DBProfiler()

    with MemorySnapshot(label="db_stress", top_n=5) as mem:
        start = time.perf_counter()
        today = time.strftime('%Y-%m-%d')

        for i in range(iterations):
            user_id = (i % 10) + 1  # 10 різних user_id
            model = "sonar-reasoning-pro"

            # SELECT
            async with db_prof.execute(
                conn,
                "SELECT count, last_reset FROM usage WHERE user_id = ? AND model_name = ?",
                (user_id, model)
            ) as cur:
                row = await cur.fetchone()

            if row:
                count, last_reset = row
                if last_reset != today:
                    async with db_prof.execute(
                        conn,
                        "UPDATE usage SET count = 1, last_reset = ? WHERE user_id = ? AND model_name = ?",
                        (today, user_id, model)
                    ):
                        pass
                elif count < 5:
                    async with db_prof.execute(
                        conn,
                        "UPDATE usage SET count = count + 1 WHERE user_id = ? AND model_name = ?",
                        (user_id, model)
                    ):
                        pass
            else:
                async with db_prof.execute(
                    conn,
                    "INSERT INTO usage (user_id, model_name, count, last_reset) VALUES (?, ?, 1, ?)",
                    (user_id, model, today)
                ):
                    pass

            await conn.commit()

        total_ms = (time.perf_counter() - start) * 1000

    await conn.close()

    db_prof.print_report(slowest_n=5)
    mem.report()

    records = db_prof.records
    avg_ms = sum(r.duration_ms for r in records) / len(records) if records else 0
    return {
        "total_ms": total_ms,
        "avg_query_ms": avg_ms,
        "peak_kb": mem.peak_kb,
        "query_count": len(records),
    }


# ---------------------------------------------------------------------------
# Сценарій 2: Memory Baseline (без AI)
# ---------------------------------------------------------------------------

async def scenario_memory_baseline() -> dict:
    """Baseline пам'яті: операції з БД та фільтрація джерел без AI-викликів.

    Вимірює:
        - Пік пам'яті при типовій роботі з даними

    Returns:
        dict: Метрики памяті {'peak_kb', 'current_kb'}.
    """
    print(f"\n{'#'*60}")
    print(f"# SCENARIO 2: Memory Baseline (no AI)")
    print(f"{'#'*60}")

    # 50 фейкових результатів пошуку
    fake_sources = [
        {
            "link": f"https://{'ukrinform.ua' if i % 3 == 0 else 'some-blog.com'}/article-{i}",
            "snippet": f"Текст результату пошуку номер {i}. Деталі події що сталась у Києві."
        }
        for i in range(50)
    ]

    with MemorySnapshot(label="memory_baseline", top_n=10) as mem:
        conn = await _create_test_db()
        today = time.strftime('%Y-%m-%d')

        # Вставляємо записи
        for uid in range(20):
            await conn.execute(
                "INSERT OR IGNORE INTO usage VALUES (?, 'sonar-reasoning-pro', 0, ?)",
                (uid, today)
            )
        await conn.commit()

        # Фільтруємо джерела (CPU-операція з рядками)
        for _ in range(10):
            verified, unverified = _mock_filter_sources(fake_sources)
            _ = "\n".join(verified + unverified)  # Симулюємо формування контексту

        await conn.close()

    mem.report()
    return {"peak_kb": mem.peak_kb, "current_kb": mem.current_kb}


# ---------------------------------------------------------------------------
# Сценарій 3: CPU — генерація пошукового запиту (mock)
# ---------------------------------------------------------------------------

def _mock_generate_query(user_text: str) -> str:
    """Mock-реалізація generate_search_query без HTTP-запиту.

    Імітує CPU-роботу: обробка рядка, токенізація, формування запиту.

    Args:
        user_text: Вхідний текст від користувача.

    Returns:
        str: Спрощений «пошуковий запит».
    """
    stop_words = {
        "і", "та", "що", "це", "на", "в", "у", "до", "від", "про", "з",
        "як", "але", "або", "тому", "якщо", "коли", "де", "хто",
    }
    words = user_text.lower().split()
    keywords = [w for w in words if w not in stop_words and len(w) > 3]
    # Симулюємо обробку (10 проходів)
    for _ in range(10):
        keywords = [w[::-1][::-1] for w in keywords]  # no-op, але витрачає CPU
    return " ".join(keywords[:6])


@profile_cpu_async(top_n=15)
async def scenario_cpu_query_generation(n_calls: int = 200) -> dict:
    """CPU-профіль: n_calls викликів mock генерації пошукового запиту.

    Вимірює:
        - CPU-час на генерацію запитів (без мережевих затримок)
        - Реальний wall-time

    Args:
        n_calls: Кількість викликів (за замовчуванням 200).

    Returns:
        dict: Метрики {'calls', 'total_wall_ms'}.
    """
    print(f"\n{'#'*60}")
    print(f"# SCENARIO 3: CPU — Query Generation ({n_calls} mock calls)")
    print(f"{'#'*60}")

    sample_texts = [
        "Зеленський підписав указ про заборону чоловікам виїжджати за кордон",
        "У Харкові стався вибух біля торгового центру, є жертви",
        "Міністерство оборони заявило про знищення 50 танків ворога",
        "Путін оголосив про повну мобілізацію у Росії",
        "У Києві розпочали будівництво нового метро на лівому березі",
    ]

    start = time.perf_counter()
    results = []
    for i in range(n_calls):
        text = sample_texts[i % len(sample_texts)]
        query = _mock_generate_query(text)
        results.append(query)
    total_ms = (time.perf_counter() - start) * 1000

    print(f"  Перший результат : '{results[0]}'")
    print(f"  Всього дзвінків  : {n_calls}")
    print(f"  Wall-time        : {total_ms:.2f} ms")
    return {"calls": n_calls, "total_wall_ms": total_ms}


# ---------------------------------------------------------------------------
# Сценарій 4: Повний pipeline (mock)
# ---------------------------------------------------------------------------

async def scenario_full_pipeline(n_requests: int = 10) -> dict:
    """Імітує повний pipeline обробки запиту: DB + фільтр + формування контексту.

    Не робить реальних AI-запитів. Вимірює CPU + пам'ять разом.

    Args:
        n_requests: Кількість «запитів» (за замовчуванням 10).

    Returns:
        dict: Метрики сценарію.
    """
    print(f"\n{'#'*60}")
    print(f"# SCENARIO 4: Full Pipeline Mock ({n_requests} requests)")
    print(f"{'#'*60}")

    conn = await _create_test_db()
    db_prof = DBProfiler()
    today = time.strftime('%Y-%m-%d')

    fake_sources = [
        {"link": f"https://ukrinform.ua/article-{i}", "snippet": f"Snippet #{i}"}
        for i in range(20)
    ] + [
        {"link": f"https://blog-{i}.com/post", "snippet": f"Blog snippet #{i}"}
        for i in range(30)
    ]

    with MemorySnapshot(label="full_pipeline", top_n=8) as mem:
        start = time.perf_counter()
        for req_i in range(n_requests):
            user_id = req_i + 1000
            claim = f"Тестове твердження номер {req_i} для перевірки фактів."

            # Step 1: DB limit check
            async with db_prof.execute(
                conn,
                "SELECT count, last_reset FROM usage WHERE user_id = ? AND model_name = ?",
                (user_id, "sonar-reasoning-pro")
            ) as cur:
                row = await cur.fetchone()

            if not row:
                async with db_prof.execute(
                    conn,
                    "INSERT INTO usage VALUES (?, 'sonar-reasoning-pro', 1, ?)",
                    (user_id, today)
                ):
                    pass
            await conn.commit()

            # Step 2: mock search query generation
            _mock_generate_query(claim)

            # Step 3: filter sources
            verified, unverified = _mock_filter_sources(fake_sources)

            # Step 4: build context (string ops)
            context = "\n".join(verified[:5] + unverified[:5])
            _ = f"Claim: {claim}\n\nContext:\n{context}"

        total_ms = (time.perf_counter() - start) * 1000

    await conn.close()
    db_prof.print_report(slowest_n=3)
    mem.report()
    print(f"  Загальний час pipeline: {total_ms:.2f} ms для {n_requests} запитів")
    print(f"  Середній час на запит : {total_ms / n_requests:.2f} ms")

    return {
        "requests": n_requests,
        "total_ms": total_ms,
        "avg_per_request_ms": total_ms / n_requests,
        "peak_kb": mem.peak_kb,
    }
