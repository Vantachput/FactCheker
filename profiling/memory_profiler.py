"""Моніторинг пам'яті для FactChecker.

Інструменти:
    - Вбудований модуль ``tracemalloc`` — відстежує виділення пам'яті Python.

Використання::

    # Варіант 1: декоратор для синхронних функцій
    @profile_memory(top_n=10)
    def my_function():
        ...

    # Варіант 2: декоратор для async-функцій
    @profile_memory_async(top_n=10)
    async def my_async_function():
        ...

    # Варіант 3: контекстний менеджер
    with MemorySnapshot(label="ai_call") as snap:
        result = some_function()
    snap.report()
"""
import functools
import tracemalloc
from typing import Callable


def _format_snapshot_diff(snapshot1: tracemalloc.Snapshot,
                           snapshot2: tracemalloc.Snapshot,
                           top_n: int = 10) -> str:
    """Форматує різницю між двома знімками пам'яті.

    Args:
        snapshot1: Початковий знімок (до виконання).
        snapshot2: Кінцевий знімок (після виконання).
        top_n: Кількість найбільших об'єктів у звіті.

    Returns:
        str: Таблиця змін у пам'яті.
    """
    top_stats = snapshot2.compare_to(snapshot1, "lineno")
    lines = [f"{'Файл':<55} {'Блоки':>8} {'Розмір':>12}"]
    lines.append("-" * 78)
    for stat in top_stats[:top_n]:
        size_kb = stat.size / 1024
        lines.append(f"{str(stat.traceback[0]):<55} {stat.count_diff:>+8} {size_kb:>+10.2f} KB")
    return "\n".join(lines)


def profile_memory(top_n: int = 10, print_report: bool = True) -> Callable:
    """Декоратор для вимірювання споживання пам'яті синхронних функцій.

    Фіксує snapshot до і після, виводить diff — блоки та байти, виділені функцією.

    Args:
        top_n: Кількість «топ» об'єктів у звіті.
        print_report: Якщо True — виводить звіт у консоль.

    Returns:
        Callable: Обгорнута функція.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            tracemalloc.start()
            snap_before = tracemalloc.take_snapshot()
            try:
                result = func(*args, **kwargs)
            finally:
                snap_after = tracemalloc.take_snapshot()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

            if print_report:
                diff = _format_snapshot_diff(snap_before, snap_after, top_n)
                print(f"\n{'='*60}")
                print(f"[MEMORY PROFILER] {func.__name__}")
                print(f"  Поточна пам'ять : {current / 1024:.2f} KB")
                print(f"  Пік пам'яті     : {peak / 1024:.2f} KB")
                print('='*60)
                print(diff)
            return result
        return wrapper
    return decorator


def profile_memory_async(top_n: int = 10, print_report: bool = True) -> Callable:
    """Декоратор для вимірювання споживання пам'яті async-функцій.

    Args:
        top_n: Кількість «топ» об'єктів у звіті.
        print_report: Якщо True — виводить звіт у консоль.

    Returns:
        Callable: Обгорнута async-функція.

    Example::

        @profile_memory_async(top_n=15)
        async def call_perplexity(claim, method, api_key, user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracemalloc.start()
            snap_before = tracemalloc.take_snapshot()
            try:
                result = await func(*args, **kwargs)
            finally:
                snap_after = tracemalloc.take_snapshot()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

            if print_report:
                diff = _format_snapshot_diff(snap_before, snap_after, top_n)
                print(f"\n{'='*60}")
                print(f"[MEMORY PROFILER ASYNC] {func.__name__}")
                print(f"  Поточна пам'ять : {current / 1024:.2f} KB")
                print(f"  Пік пам'яті     : {peak / 1024:.2f} KB")
                print('='*60)
                print(diff)
            return result
        return wrapper
    return decorator


class MemorySnapshot:
    """Контекстний менеджер для вимірювання пам'яті в блоці коду.

    Example::

        with MemorySnapshot(label="db_stress_test") as snap:
            for i in range(100):
                do_something()
        snap.report()
    """

    def __init__(self, label: str = "block", top_n: int = 10):
        """Ініціалізує менеджер.

        Args:
            label: Назва блоку для звіту.
            top_n: Кількість найбільших об'єктів у звіті.
        """
        self.label = label
        self.top_n = top_n
        self._snap_before = None
        self._snap_after = None
        self.current_kb = 0.0
        self.peak_kb = 0.0

    def __enter__(self):
        tracemalloc.start()
        self._snap_before = tracemalloc.take_snapshot()
        return self

    def __exit__(self, *_):
        self._snap_after = tracemalloc.take_snapshot()
        current, peak = tracemalloc.get_traced_memory()
        self.current_kb = current / 1024
        self.peak_kb = peak / 1024
        tracemalloc.stop()

    def report(self) -> str:
        """Виводить звіт у консоль та повертає його як рядок.

        Returns:
            str: Текстовий звіт.
        """
        diff = _format_snapshot_diff(self._snap_before, self._snap_after, self.top_n)
        header = (
            f"\n{'='*60}\n"
            f"[MEMORY SNAPSHOT] {self.label}\n"
            f"  Поточна пам'ять : {self.current_kb:.2f} KB\n"
            f"  Пік пам'яті     : {self.peak_kb:.2f} KB\n"
            f"{'='*60}\n"
        )
        output = header + diff
        print(output)
        return output
