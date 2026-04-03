"""Профілювання SQLite-запитів для FactChecker.

Інструменти:
    - ``time.perf_counter`` — вимірювання часу виконання кожного запиту.
    - ``aiosqlite`` — async-обгортка для SQLite.

Модуль надає:
    - ``traced_execute`` — замінна для ``conn.execute()``, що логує час.
    - ``DBProfiler`` — клас-менеджер сесії профілювання зі зведеним звітом.

Використання::

    # Варіант 1: разовий traced_execute
    async with traced_execute(conn, "SELECT ...", params) as cursor:
        row = await cursor.fetchone()

    # Варіант 2: сесія профілювання з підсумком
    profiler = DBProfiler()
    async with profiler.execute(conn, "SELECT ...", params) as cursor:
        ...
    profiler.print_report()
"""
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryRecord:
    """Запис одного SQL-запиту.

    Attributes:
        sql: Текст SQL-запиту.
        params: Параметри запиту.
        duration_ms: Тривалість виконання (мілісекунди).
        rows_affected: Кількість повернених / змінених рядків.
    """
    sql: str
    params: tuple
    duration_ms: float
    rows_affected: int = 0


@dataclass
class DBProfiler:
    """Менеджер сесії профілювання БД.

    Збирає статистику по всіх виконаних запитах і формує зведений звіт.

    Attributes:
        records: Список записів виконаних запитів.

    Example::

        db_prof = DBProfiler()
        async with db_prof.execute(conn, "SELECT * FROM usage WHERE user_id = ?", (42,)) as cur:
            rows = await cur.fetchall()
        db_prof.print_report()
    """
    records: list[QueryRecord] = field(default_factory=list)

    @asynccontextmanager
    async def execute(self, conn, sql: str, params: tuple = ()):
        """Виконує SQL-запит, вимірюючи час і зберігаючи статистику.

        Args:
            conn: Активне aiosqlite-з'єднання.
            sql: SQL-запит.
            params: Параметри запиту.

        Yields:
            aiosqlite.Cursor: Курсор з результатом.
        """
        start = time.perf_counter()
        async with conn.execute(sql, params) as cursor:
            elapsed_ms = (time.perf_counter() - start) * 1000
            rows = cursor.rowcount if cursor.rowcount >= 0 else 0
            self.records.append(QueryRecord(
                sql=sql.strip(),
                params=params,
                duration_ms=elapsed_ms,
                rows_affected=rows,
            ))
            yield cursor

    def print_report(self, slowest_n: int = 5) -> None:
        """Виводить зведений звіт за сесію профілювання.

        Args:
            slowest_n: Кількість найповільніших запитів у підсумку.
        """
        if not self.records:
            print("[DB PROFILER] Немає записаних запитів.")
            return

        total_ms = sum(r.duration_ms for r in self.records)
        avg_ms = total_ms / len(self.records)
        sorted_records = sorted(self.records, key=lambda r: r.duration_ms, reverse=True)

        print(f"\n{'='*65}")
        print(f"[DB PROFILER] Зведений звіт — {len(self.records)} запитів")
        print(f"  Загальний час  : {total_ms:.3f} ms")
        print(f"  Середній час   : {avg_ms:.3f} ms")
        print(f"  Найдовший      : {sorted_records[0].duration_ms:.3f} ms")
        print(f"\n  Топ-{slowest_n} найповільніших запитів:")
        print(f"  {'Час (ms)':>10}  {'SQL':}")
        print(f"  {'-'*10}  {'-'*40}")
        for rec in sorted_records[:slowest_n]:
            short_sql = rec.sql[:70].replace("\n", " ")
            print(f"  {rec.duration_ms:>10.3f}  {short_sql}")
        print('='*65)

    def reset(self) -> None:
        """Очищає всі записи поточної сесії."""
        self.records.clear()


@asynccontextmanager
async def traced_execute(conn, sql: str, params: tuple = (), label: str = ""):
    """Разова обгортка для ``conn.execute()`` з логуванням часу.

    Args:
        conn: Активне aiosqlite-з'єднання.
        sql: SQL-запит.
        params: Параметри запиту.
        label: Додаткова мітка для рядка у консолі.

    Yields:
        aiosqlite.Cursor: Курсор з результатом.

    Example::

        async with traced_execute(conn, "SELECT count FROM usage WHERE user_id = ?", (uid,)) as cur:
            row = await cur.fetchone()
    """
    start = time.perf_counter()
    async with conn.execute(sql, params) as cursor:
        elapsed_ms = (time.perf_counter() - start) * 1000
        tag = f"[{label}] " if label else ""
        short_sql = sql.strip()[:80].replace("\n", " ")
        print(f"  {tag}DB query ({elapsed_ms:.3f} ms): {short_sql}")
        yield cursor
