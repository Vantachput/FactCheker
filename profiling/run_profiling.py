"""Точка входу для профілювання FactChecker.

Запускає всі тестові сценарії та виводить зведений звіт.

Використання::

    # Через Makefile
    make profile

    # Напряму
    python -m profiling.run_profiling

    # З кореня проекту
    python profiling/run_profiling.py
"""
import asyncio
import sys
import time
from pathlib import Path

# Дозволяємо запуск з кореня проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from profiling.scenarios import (
    scenario_cpu_query_generation,
    scenario_db_stress,
    scenario_full_pipeline,
    scenario_memory_baseline,
)

SEPARATOR = "=" * 65


async def run_all() -> None:
    """Виконує всі профілювальні сценарії та виводить зведену таблицю."""
    print(f"\n{SEPARATOR}")
    print("  FactChecker — Performance Profiling Suite")
    print(f"  Python {sys.version.split()[0]}")
    print(SEPARATOR)

    results = {}
    suite_start = time.perf_counter()

    # --- Сценарій 1: DB Stress ---
    try:
        results["db_stress"] = await scenario_db_stress(iterations=100)
    except Exception as e:
        print(f"[ERROR] scenario_db_stress: {e}")
        results["db_stress"] = {}

    # --- Сценарій 2: Memory Baseline ---
    try:
        results["memory_baseline"] = await scenario_memory_baseline()
    except Exception as e:
        print(f"[ERROR] scenario_memory_baseline: {e}")
        results["memory_baseline"] = {}

    # --- Сценарій 3: CPU Query Generation ---
    try:
        results["cpu_queries"] = await scenario_cpu_query_generation(n_calls=200)
    except Exception as e:
        print(f"[ERROR] scenario_cpu_query_generation: {e}")
        results["cpu_queries"] = {}

    # --- Сценарій 4: Full Pipeline ---
    try:
        results["full_pipeline"] = await scenario_full_pipeline(n_requests=10)
    except Exception as e:
        print(f"[ERROR] scenario_full_pipeline: {e}")
        results["full_pipeline"] = {}

    suite_ms = (time.perf_counter() - suite_start) * 1000

    # -----------------------------------------------------------------------
    # Зведений звіт
    # -----------------------------------------------------------------------
    print(f"\n{SEPARATOR}")
    print("  ЗВЕДЕНИЙ ЗВІТ ПРОФІЛЮВАННЯ")
    print(SEPARATOR)

    db = results.get("db_stress", {})
    mem = results.get("memory_baseline", {})
    cpu = results.get("cpu_queries", {})
    pip = results.get("full_pipeline", {})

    rows = [
        ("DB Stress (100 ітерацій)",
         f"{db.get('total_ms', 0):.1f} ms",
         f"avg query: {db.get('avg_query_ms', 0):.3f} ms",
         f"пік пам'яті: {db.get('peak_kb', 0):.1f} KB"),

        ("Memory Baseline",
         "—",
         f"пік: {mem.get('peak_kb', 0):.1f} KB",
         f"поточна: {mem.get('current_kb', 0):.1f} KB"),

        ("CPU Query Gen (200 викликів)",
         f"{cpu.get('total_wall_ms', 0):.1f} ms",
         f"avg: {cpu.get('total_wall_ms', 0) / max(cpu.get('calls', 1), 1):.3f} ms",
         "—"),

        ("Full Pipeline (10 запитів)",
         f"{pip.get('total_ms', 0):.1f} ms",
         f"avg/req: {pip.get('avg_per_request_ms', 0):.1f} ms",
         f"пік пам'яті: {pip.get('peak_kb', 0):.1f} KB"),
    ]

    header = f"  {'Сценарій':<32} {'Час':>12} {'Деталі':>22} {'Пам-ять':>18}"
    print(header)
    print(f"  {'-'*32} {'-'*12} {'-'*22} {'-'*18}")
    for name, time_val, detail, memory in rows:
        print(f"  {name:<32} {time_val:>12} {detail:>22} {memory:>18}")

    print(f"\n  Загальний час suite : {suite_ms:.0f} ms")
    print(SEPARATOR)
    print("  Профілювання завершено успішно.")
    print(SEPARATOR)


def main() -> None:
    """Синхронна точка входу."""
    asyncio.run(run_all())


if __name__ == "__main__":
    main()
