"""Модуль обробки базових команд бота (наприклад, /start).

Відповідає за початкову ініціалізацію стану користувача та 
відображення головного меню з інструкціями.
"""
from telegram import Update
from telegram.ext import ContextTypes

from utils.keyboards import get_main_menu


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, user_states: dict):
    """Обробник команди /start.
    
    Скидає або ініціалізує стан користувача, встановлюючи метод "base" 
    за замовчуванням. Відправляє вітальне повідомлення з головним меню.

    Args:
        update (telegram.Update): Запит оновлення від клієнта.
        context (telegram.ext.ContextTypes.DEFAULT_TYPE): Контекст бота.
        user_states (dict): Глобальний словник для зберігання станів сесій.
    """
    user_states[update.effective_user.id] = {"method": "base", "action": None}
    start_text = (
        "🤖 **Вас вітає Центр Перевірки Фактів (AI Fact-Checker)**\n\n"
        "Я допоможу вам розпізнати маніпуляції та перевірити новини "
        "на достовірність.\n\n"
        "🔍 **Як працювати з ботом:**\n"
        "1. Натисніть кнопку **'Класифікувати новину'**.\n"
        "2. Надішліть текст, посилання або перешліть пост.\n"
        "3. Отримайте детальний аналіз та вердикт.\n\n"
        "⚙️ **Доступні методи (у налаштуваннях):**\n"
        "• `Base` — Швидка перевірка через Google та GPT.\n"
        "• `Web-search` — Глибокий пошук у реальному часі (Perplexity).\n"
        "• `Fine-tuning` — Аналіз навченими моделями Llama 3.1 та GPT-4o-mini.\n\n"
        "⚡ *Зараз встановлено метод: Base*"
    )
    
    await update.message.reply_text(
        start_text, 
        reply_markup=get_main_menu(), 
        parse_mode="Markdown"
    )