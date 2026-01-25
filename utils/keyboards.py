from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Класифікувати новину", callback_data="menu_classify")],
        [InlineKeyboardButton("⚙️ Обрати спосіб та модель", callback_data="menu_settings")],
        [InlineKeyboardButton("ℹ️ Справка", callback_data="menu_help")]
    ])

def get_settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Fine-tuning (Навчені моделі)", callback_data="menu_ft")],
        [InlineKeyboardButton("🌐 Web-search (Perplexity)", callback_data="set_web")],
        [InlineKeyboardButton("🔎 Base (Serper + GPT)", callback_data="set_base")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

def get_ft_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🦙 Llama 3.1 (Together)", callback_data="set_ft_together")],
        [InlineKeyboardButton("🤖 GPT-4o-mini (OpenAI FT)", callback_data="set_ft_openai")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu_settings")]
    ])

def get_pplx_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Sonar (Безліміт)", callback_data="set_pplx_sonar")],
        [InlineKeyboardButton("🧠 Reasoning Pro (10/день)", callback_data="set_pplx_reasoning")],
        [InlineKeyboardButton("🔬 Deep Research (1/день)", callback_data="set_pplx_deep")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu_settings")]
    ])

def get_back_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Скасувати та Назад", callback_data="main_menu")]])