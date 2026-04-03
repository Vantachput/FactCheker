"""CPU-профілювання для FactChecker.

Інструменти:
    - Вбудований модуль ``cProfile`` — детальна статистика викликів функцій.
    - Вбудований модуль ``pstats`` — форматування та сортування звітів.

Використання::

    # Варіант 1: декоратор для звичайних функцій
    @profile_cpu(top_n=10)
    def my_function():
        ...

    # Варіант 2: декоратор для async функцій
    @profile_cpu_async(top_n=10)
    async def my_async_function():
        ...

    # Варіант 3: ручний запуск
    stats = profile_function(my_func, arg1, arg2)
"""
import cProfile
import functools
import io
import pstats
import time
from typing import Callable


def _format_stats(profiler: cProfile.Profile, top_n: int = 20) -> str:
    """Форматує статистику cProfile у рядок.

    Args:
        profiler: Активний екземпляр cProfile.Profile.
        top_n: Кількість рядків у звіті (топ найповільніших функцій).

    Returns:
        str: Відформатований текстовий звіт.
    """
    stream = io.StringIO()
    ps = pstats.Stats(profiler, stream=stream)
    ps.strip_dirs()
    ps.sort_stats(pstats.SortKey.CUMULATIVE)
    ps.print_stats(top_n)
    return stream.getvalue()


def profile_cpu(top_n: int = 20, print_report: bool = True) -> Callable:
    """Декоратор для CPU-профілювання синхронних функцій.

    Args:
        top_n: Кількість рядків у звіті.
        print_report: Якщо True — одразу виводить звіт у консоль.

    Returns:
        Callable: Обгорнута функція.

    Example::

        @profile_cpu(top_n=15)
        def generate_query(text: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()
                elapsed = time.perf_counter() - start

            report = _format_stats(profiler, top_n)
            if print_report:
                print(f"\n{'='*60}")
                print(f"[CPU PROFILER] {func.__name__} — {elapsed:.4f}s")
                print('='*60)
                print(report)
            return result
        return wrapper
    return decorator


def profile_cpu_async(top_n: int = 20, print_report: bool = True) -> Callable:
    """Декоратор CPU-профілювання для async-функцій.

    Оскільки cProfile не підтримує нативний профіль coroutine,
    використовується ``perf_counter`` для загального часу виконання та
    cProfile для синхронної частини (CPU bound work).

    Args:
        top_n: Кількість рядків у звіті.
        print_report: Якщо True — одразу виводить звіт у консоль.

    Returns:
        Callable: Обгорнута async-функція.

    Example::

        @profile_cpu_async(top_n=20)
        async def call_base_gpt(claim, verified_srcs, unverified_srcs, model_id, user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            finally:
                profiler.disable()
                elapsed = time.perf_counter() - start

            report = _format_stats(profiler, top_n)
            if print_report:
                print(f"\n{'='*60}")
                print(f"[CPU PROFILER ASYNC] {func.__name__} — wall time: {elapsed:.4f}s")
                print('='*60)
                print(report)
            return result
        return wrapper
    return decorator


def profile_function(func: Callable, *args, top_n: int = 20, **kwargs):
    """Запускає функцію під cProfile без декоратора та повертає результат і звіт.

    Args:
        func: Функція для профілювання.
        *args: Аргументи для func.
        top_n: Кількість рядків у звіті.
        **kwargs: Іменовані аргументи для func.

    Returns:
        tuple[Any, str]: (результат функції, текстовий звіт cProfile)

    Example::

        result, report = profile_function(process_text, "деякий текст")
        print(report)
    """
    profiler = cProfile.Profile()
    profiler.enable()
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()
        elapsed = time.perf_counter() - start

    report = _format_stats(profiler, top_n)
    print(f"\n[CPU PROFILER] {func.__name__} — {elapsed:.4f}s\n{report}")
    return result, report
