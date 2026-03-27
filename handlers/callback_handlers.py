from utils.keyboards import (
    get_back_button,
    get_ft_menu,
    get_main_menu,
    get_pplx_menu,
    get_settings_menu,
)


async def handle_callback(update, context, user_states):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    if uid not in user_states:
        user_states[uid] = {"method": "base", "action": None}

    if query.data == "main_menu":
        user_states[uid]["action"] = None
        await query.edit_message_text("Головне меню:", reply_markup=get_main_menu())

    elif query.data == "menu_settings":
        await query.edit_message_text(
            "Оберіть категорію:", reply_markup=get_settings_menu()
        )

    elif query.data == "menu_ft":
        await query.edit_message_text(
            "Оберіть навчену модель:", reply_markup=get_ft_menu()
        )

    elif query.data == "set_ft_together":
        user_states[uid]["method"] = "together"
        await query.edit_message_text(
            "✅ Обрано Fine-tune: Llama 3.1", reply_markup=get_main_menu()
        )

    elif query.data == "set_ft_openai":
        user_states[uid]["method"] = "openai_ft"
        await query.edit_message_text(
            "✅ Обрано Fine-tune: GPT-4o-mini", reply_markup=get_main_menu()
        )

    elif query.data == "set_web":
        await query.edit_message_text(
            "Оберіть модель Perplexity:", reply_markup=get_pplx_menu()
        )

    elif query.data == "set_base":
        user_states[uid]["method"] = "base"
        await query.edit_message_text(
            "✅ Обрано Base (Serper + GPT)", reply_markup=get_main_menu()
        )

    elif query.data.startswith("set_pplx_"):
        m = (
            query.data.replace("set_pplx_", "")
            .replace("reasoning", "sonar-reasoning-pro")
            .replace("deep", "sonar-deep-research")
        )
        user_states[uid]["method"] = m
        await query.edit_message_text(
            f"✅ Обрано Perplexity: **{m}**",
            reply_markup=get_main_menu(),
            parse_mode="Markdown",
        )

    elif query.data == "menu_classify":
        user_states[uid]["action"] = "WAITING"
        await query.edit_message_text(
            "📝 **Надішліть текст новини для аналізу.**",
            reply_markup=get_back_button(),
            parse_mode="Markdown",
        )

    elif query.data == "menu_help":
        help_text = (
            "📖 **Посібник користувача AI Fact-Checker**\n\n"
            "Я — ваш персональний цифровий детектив 🕵️‍♂️. "
            "Моє завдання — допомагати вам орієнтуватися "
            "в океані інформації та вираховувати маніпуляції.\n\n"
            "🚀 **Які методи аналізу я маю?**\n\n"
            "1️⃣ **🔎 Base (Швидка перевірка)**\n"
            "Оптимальний вибір для щоденних новин. Я миттєво "
            "«гуглю» інформацію через Serper та звіряю її "
            "з базою довірених джерел (ЗМІ категорії A/A+).\n\n"
            "2️⃣ **🌐 Web-search (Глибокий пошук)**\n"
            "Використовує потужність **Perplexity**. Це як "
            "консиліум аналітиків, які перевіряють факти в "
            "реальному часі по всьому інтернету. Найкраще "
            "підходить для свіжих подій, що сталися щойно.\n\n"
            "3️⃣ **🎯 Fine-tuning (Експертні моделі)**\n"
            "Це моделі (Llama 3.1, GPT-4o-mini), які пройшли "
            "спеціальне «тренування» на великих архівах "
            "реальних фейків та маніпуляцій. Вони бачать "
            "структуру брехні навіть там, де вона прихована.\n\n"
            "--- \n"
            "💡 **Порада:** Якщо новина викликає сильні емоції "
            "(гнів, паніку, надмірну радість) — це перша "
            "ознака того, що її варто перевірити через "
            "метод **Reasoning Pro** 🧠.\n\n"
            "⚠️ *Пам'ятайте: ШІ — це помічник, а не істина в "
            "останній інстанції. Завжди зберігайте критичне "
            "мислення!* 🧩"
        )
        await query.edit_message_text(
            help_text, reply_markup=get_main_menu(), parse_mode="Markdown"
        )