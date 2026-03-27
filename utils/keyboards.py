"""Набір функцій для управління клавіатурами бота.

Цей модуль містить чисті функції, кожна з яких повертає 
об'єкт `InlineKeyboardMarkup` з відповідними кнопками для 
меню Fact-Checker'а.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    """Повертає головне меню бота.
    
    Returns:
        InlineKeyboardMarkup: Клавіатура з трьома кнопками: Класифікувати,
            Обрати спосіб, Довідка.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Класифікувати", callback_data="menu_classify")],
        [InlineKeyboardButton("⚙️ Обрати спосіб", callback_data="menu_settings")],
        [InlineKeyboardButton("ℹ️ Справка", callback_data="menu_help")]
    ])

def get_settings_menu() -> InlineKeyboardMarkup:
    """Повертає меню вибору категорії методу аналізу.
    
    Returns:
        InlineKeyboardMarkup: Кнопки Fine-tuning, Web-search, Base.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Fine-tuning", callback_data="menu_ft")],
        [InlineKeyboardButton("🌐 Web-search (Pplx)", callback_data="set_web")],
        [InlineKeyboardButton("🔎 Base (Serper+GPT)", callback_data="set_base")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

def get_ft_menu() -> InlineKeyboardMarkup:
    """Повертає меню вибору навчених (Fine-tuned) моделей.
    
    Returns:
        InlineKeyboardMarkup: Кнопки для Llama та GPT-4o-mini.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🦙 Llama 3.1 8B", callback_data="set_ft_together")],
        [InlineKeyboardButton("🤖 GPT-4o-mini", callback_data="set_ft_openai")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu_settings")]
    ])

def get_pplx_menu() -> InlineKeyboardMarkup:
    """Повертає меню вибору моделей Perplexity.
    
    Returns:
        InlineKeyboardMarkup: Кнопки для Sonar, Reasoning, Deep Research.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Sonar (Базовий)", callback_data="set_pplx_sonar")],
        [InlineKeyboardButton("🧠 Reasoning Pro", callback_data="set_pplx_reasoning")],
        [InlineKeyboardButton("🔬 Deep Research", callback_data="set_pplx_deep")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu_settings")]
    ])

def get_back_button() -> InlineKeyboardMarkup:
    """Повертає клавіатуру лише з кнопкою 'Скасувати'.
    
    Returns:
        InlineKeyboardMarkup: Кнопка відміни поточної дії.
    """
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Скасувати", callback_data="main_menu")]
    ])