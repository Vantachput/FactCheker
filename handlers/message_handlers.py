"""Модуль обробки текстових повідомлень і запитів на перевірку.

**Бізнес-логіка (Механізм перевірки та Fallback):**
Коли користувач надсилає новину (прямим текстом або пересилає повідомлення),
цей модуль виконує наступне:
1. Парсить джерело (чи репост це з каналу/групи).
2. Записує стан користувача (перевіряє ліміти).
3. Якщо метод - `base`, спочатку генерується розумний запит. Якщо розумний запит 
   не дає результатів у Google (наприклад, фейк дуже абстрактний), спрацьовує 
   **Fallback-алгоритм**: береться прямий текст новини (перші слова) і 
   надсилається в Google, щоб знайти хоч якісь спростування.
4. Розбиває великі відповіді (понад 4000 символів) на частини через `send_smart_reply`.
"""
import os

from telegram import LinkPreviewOptions

from database.db_manager import check_and_increment_limit
from services.ai_service import (
    call_base_gpt,
    call_openai_ft,
    call_perplexity,
    call_together,
    generate_search_query,
)
from services.search_service import filter_sources, serper_search
from utils.helpers import get_progress_bar, split_text
from utils.keyboards import get_main_menu


async def send_smart_reply(update, text: str, status_msg=None):
    """Відправляє великі повідомлення частинами.
    
    Оскільки Telegram обмежує розмір одного повідомлення 4096 символами, 
    ця функція розбиває текст на фрагменти, гарантуючи, що прев'ю посилання
    (LinkPreview) з'явиться лише на першому повідомленні (щоб не спамити).

    Args:
        update: Запит оновлення.
        text (str): Великий текст для відправки.
        status_msg (optional): Повідомлення зі статусом ("Аналізую..."), 
                               яке буде замінено на результат. Якщо None, 
                               надсилається як Reply.
    """
    MAX_LEN = 4000
    
    # Налаштування для відображення посилання (фрейму)
    # prefer_large_media=True зробить ту саму велику картинку, якщо вона є на сайті
    link_preview_cfg = LinkPreviewOptions(
        is_disabled=False, 
        prefer_large_media=True, 
        show_above_text=False
    )
    
    if len(text) <= MAX_LEN:
        content = f"⚖️ **Результат:**\n\n{text}"
        if status_msg:
            await status_msg.edit_text(
                content, 
                parse_mode="Markdown", 
                link_preview_options=link_preview_cfg
            )
        else:
            await update.message.reply_text(
                content, 
                parse_mode="Markdown", 
                link_preview_options=link_preview_cfg
            )
    else:
        parts = split_text(text)
        
        # Для першої частини вмикаємо прев'ю
        first_part = f"⚖️ **Результат (Ч. 1):**\n\n{parts[0]}"
        if status_msg:
            await status_msg.edit_text(
                first_part, 
                parse_mode="Markdown", 
                link_preview_options=link_preview_cfg
            )
        else:
            await update.message.reply_text(
                first_part, 
                parse_mode="Markdown", 
                link_preview_options=link_preview_cfg
            )
            
        # Для наступних частин вимикаємо прев'ю, щоб не спамити фреймами
        no_preview = LinkPreviewOptions(is_disabled=True)
        for i, part in enumerate(parts[1:], 2):
            await update.message.reply_text(
                f"⚖️ **Результат (Ч. {i}):**\n\n{part}", 
                parse_mode="Markdown",
                link_preview_options=no_preview
            )

async def handle_message(update, context, user_states: dict):
    """Головний обробник контенту (новин) від користувачів.
    
    Перевіряє, чи знаходиться користувач в стані `WAITING` (тобто натиснув 
    "Класифікувати новину"). Якщо так, витягує текст або підпис до медіа, 
    визначає джерело репосту, надсилає запит через обраний метод AI 
    (Together, OpenAI, Serper, Perplexity) та повертає результат.

    Args:
        update: Запит оновлення від клієнта (містить повідомлення).
        context: Контекст бота від telegram.ext.
        user_states (dict): Стан користувача.
    """
    uid = update.effective_user.id
    
    state = user_states.get(uid, {})
    
    if state.get("action") == "WAITING":
        try:
            # 1. Універсальне отримання тексту
            # Важливо: використовуємо getattr, щоб уникнути помилок, 
            # якщо message чомусь порожній
            msg = update.message
            raw_text = msg.text or msg.caption or ""
            
            # 2. Визначення джерела (репост чи ні) з перевірками на None
            claim = raw_text
            origin = msg.forward_origin
            if origin:
                if origin.type == "channel":
                    # Репост із каналу
                    source = origin.chat.title or origin.chat.username or "Канал"
                    claim = f"Новина з джерела ({source}): {raw_text}"
                elif origin.type == "hidden_user":
                    # Репост від користувача, який приховав профіль
                    claim = (
                        f"Переслана новина від {origin.sender_user_name}: "
                        f"{raw_text}"
                    )
                elif origin.type == "user":
                    # Репост від конкретного користувача
                    source = origin.sender_user.first_name or "Користувач"
                    claim = f"Переслана новина від {source}: {raw_text}"
                elif origin.type == "chat":
                    # Репост із групи
                    source = origin.sender_chat.title or "Група"
                    claim = f"Переслана новина з ({source}): {raw_text}"

            # 3. Перевірка на порожній текст
            if not claim.strip():
                await msg.reply_text("❌ Помилка: Повідомлення не містить тексту.")
                return

            method = state.get("method", "base")
            
            # Безпечне отримання ADMIN_ID
            admin_str = os.getenv("ADMIN_ID", "0")
            admin_id = int(admin_str) if admin_str.isdigit() else 0
            
            # 4. Надсилаємо статус (Тут ми дізнаємось, чи працює відправка)
            status_msg = await msg.reply_text(f"⏳ Аналізую через {method}...")

            # --- ПОЧАТОК АНАЛІЗУ ---
            allowed, l_val = await check_and_increment_limit(uid, method, admin_id)
            if not allowed:
                await status_msg.edit_text(
                    f"🚫 Ліміт вичерпано. Для цього методу доступно "
                    f"{l_val} запитів на день.", 
                    reply_markup=get_main_menu()
                )
                return

            res = ""
            if method == "together":
                res = await call_together(claim, os.getenv("MODEL_TOGETHER_FT"), uid)
                res += get_progress_bar(res)

            elif method == "openai_ft":
                model_id = os.getenv("MODEL_GPT_4_1_mini")
                if not model_id:
                    res = "⚠️ Помилка: ID моделі не знайдено в .env"
                else:
                    res = await call_openai_ft(claim, model_id, uid)
                    res += get_progress_bar(res)

            elif method == "base":
                # 1. Спроба знайти подію за "розумним" запитом
                search_query = await generate_search_query(claim)
                print(f"Attempt 1 Query: {search_query}") # Для дебагу
                
                raw = await serper_search(search_query, os.getenv("SERPER_API_KEY"))
                
                # 2. УНІВЕРСАЛЬНИЙ FALLBACK:
                # Якщо результатів 0, значить запит був занадто розумним 
                # або події не існує.
                # Спробуємо знайти хоча б згадку джерела або ключових імен.
                if not raw:
                    print("Attempt 1 failed. Trying broad search...")
                    # Простий алгоритм: беремо перші 30 слів тексту, 
                    # щоб Google сам розібрався
                    fallback_query = claim.replace("\n", " ")[:200]
                    raw = await serper_search(
                        fallback_query, os.getenv("SERPER_API_KEY")
                    )

                verified, unverified = filter_sources(raw)
                res = await call_base_gpt(
                    claim, verified, unverified, os.getenv("MODEL_NAME"), uid
                )
            
            else: # Perplexity
                res = await call_perplexity(
                    claim, method, os.getenv("PERPLEXITY_API_KEY"), uid
                )

            await send_smart_reply(update, res, status_msg)
            await context.bot.send_message(
                chat_id=uid,
                text="✅ Аналіз завершено. Оберіть наступну дію:",
                reply_markup=get_main_menu()
            )

        except Exception as e:
            # Це зловить будь-яку помилку (наприклад, Markdown або API)
            print(f"КРИТИЧНА ПОМИЛКА: {e}")
            if 'status_msg' in locals():
                await status_msg.edit_text(
                    f"❌ Помилка: {str(e)[:100]}", 
                    reply_markup=get_main_menu()
                )
            else:
                await update.message.reply_text(
                    f"❌ Сталася помилка: {str(e)[:100]}", 
                    reply_markup=get_main_menu()
                )
        
        # Скидаємо стан тільки після завершення (або помилки)
        user_states[uid]["action"] = None
    else:
        await update.message.reply_text(
            "Оберіть дію в меню.", reply_markup=get_main_menu()
        )