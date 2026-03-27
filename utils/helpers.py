"""Допоміжні утиліти для обробки тексту та часу.

Цей модуль містить чисті функції (pure functions), які використовуються
для форматування відповідей, розбиття тексту для Telegram, екранування 
символів та роботи з локальним часом України.

Тести (doctest):
    Ви можете запустити тести цього модуля командою:
    `python -m doctest utils/helpers.py -v`
"""
import re
from datetime import datetime

import pytz


def split_text(text: str, max_length: int = 4000) -> list[str]:
    """Розбиває текст на фрагменти вказаної довжини.
    
    Telegram має обмеження на розмір одного повідомлення (4096 символів).
    Ця функція дозволяє гарантовано розбити великий текст на частини.

    Args:
        text (str): Вхідний текст для розбиття.
        max_length (int, optional): Максимальна довжина одного фрагмента. За замовчуванням 4000.

    Returns:
        list[str]: Список текстових фрагментів.

    Examples:
        >>> split_text("1234567890", max_length=3)
        ['123', '456', '789', '0']
        >>> split_text("", max_length=5)
        []
    """
    if not text:
        return []
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def get_progress_bar(text: str) -> str:
    """Генерує візуальну шкалу впевненості ШІ (до 10 блоків).
    
    Функція шукає у тексті згадку відсотка (наприклад, "85%"), і перетворює
    це число на рядок з емодзі-квадратиками.

    Args:
        text (str): Вхідний текст від AI, що містить відсоток впевненості.

    Returns:
        str: Відформатований рядок зі шкалою, або порожній рядок, якщо відсоток не знайдено.

    Examples:
        >>> get_progress_bar("Впевненість: 87%")
        '\\n\\n📊 Шкала впевненості ШІ:\\n🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜ 87%'
        >>> get_progress_bar("Без відсотків")
        ''
    """
    match = re.search(r'(\d+)%', text)
    if match:
        percent = int(match.group(1))
        percent = min(100, max(0, percent)) # обмежуємо 0..100
        filled = int(percent / 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)
        return f"\n\n📊 Шкала впевненості ШІ:\n{bar} {percent}%"
    return ""

def escape_markdown(text: str) -> str:
    r"""Екранує спеціальні символи Markdown для безпечної відправки в Telegram.
    
    Telegram боти можуть викликати помилку `ParseError`, якщо відправити
    повідомлення з непарними або неправильно відформатованими символами Markdown.
    
    Args:
        text (str): Оригінальний текст.

    Returns:
        str: Текст з екранованими символами `_`, `*`, `[`.
        
    Examples:
        >>> escape_markdown("Текст з _курсивом_ та *жирним* шрифтом [Лінк]")
        'Текст з \\_курсивом\\_ та \\*жирним\\* шрифтом \\[Лінк]'
    """
    if not text:
        return ""
    parse_fix = text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[")
    return parse_fix

def get_ukraine_time() -> str:
    """Отримує поточний локальний час в Україні.
    
    Використовує часовий пояс `Europe/Kyiv`.

    Returns:
        str: Рядок формату `DD.MM.YYYY HH:MM`.
    """
    tz_ua = pytz.timezone('Europe/Kyiv')
    now_ua = datetime.now(tz_ua)
    return now_ua.strftime("%d.%m.%Y %H:%M")