from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Класифікувати", callback_data="menu_classify")],
        [InlineKeyboardButton("⚙️ Обрати спосіб", callback_data="menu_settings")],
        [InlineKeyboardButton("ℹ️ Справка", callback_data="menu_help")]
    ])

def get_settings_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Fine-tuning", callback_data="menu_ft")],
        [InlineKeyboardButton("🌐 Web-search (Pplx)", callback_data="set_web")],
        [InlineKeyboardButton("🔎 Base (Serper+GPT)", callback_data="set_base")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="main_menu")]
    ])

def get_ft_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🦙 Llama 3.1 8B", callback_data="set_ft_together")],
        [InlineKeyboardButton("🤖 GPT-4o-mini", callback_data="set_ft_openai")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu_settings")]
    ])

def get_pplx_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Sonar (Базовий)", callback_data="set_pplx_sonar")],
        [InlineKeyboardButton("🧠 Reasoning Pro", callback_data="set_pplx_reasoning")],
        [InlineKeyboardButton("🔬 Deep Research", callback_data="set_pplx_deep")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="menu_settings")]
    ])

def get_back_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Скасувати", callback_data="main_menu")]
    ])