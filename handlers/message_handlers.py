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

from utils.logger import logger

from database.db_manager import check_and_increment_limit
from services.ai_service import (
    analyze_image_from_url,
    analyze_video_with_together,
    call_base_gpt,
    call_openai_ft,
    call_perplexity,
    call_together,
    extract_text_from_image,
    extract_factors_from_video_analysis,
    generate_search_query,
)
from services.search_service import filter_sources, serper_search
from services.threads_service import ThreadsService
from utils.helpers import get_progress_bar, split_text, convert_to_wav
from utils.keyboards import get_main_menu
from services.deepgram_service import transcribe_audio
import tempfile

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
    link_preview_cfg = LinkPreviewOptions(
        is_disabled=False, 
        prefer_large_media=True, 
        show_above_text=False
    )
    no_preview = LinkPreviewOptions(is_disabled=True)
    
    async def _safe_send(content, is_edit=False, preview_opts=None):
        try:
            if is_edit and status_msg:
                await status_msg.edit_text(content, parse_mode="Markdown", link_preview_options=preview_opts)
            else:
                await update.message.reply_text(content, parse_mode="Markdown", link_preview_options=preview_opts)
        except Exception as e:
            # Fallback for Markdown parse errors (unclosed entities)
            if "parse" in str(e).lower() or "entity" in str(e).lower() or "markdown" in str(e).lower():
                logger.warning(f"Markdown parse error, falling back to raw text. Error: {e}")
                if is_edit and status_msg:
                    await status_msg.edit_text(content, link_preview_options=preview_opts)
                else:
                    await update.message.reply_text(content, link_preview_options=preview_opts)
            else:
                raise e

    if len(text) <= MAX_LEN:
        content = f"⚖️ **Результат:**\n\n{text}"
        await _safe_send(content, is_edit=bool(status_msg), preview_opts=link_preview_cfg)
    else:
        parts = split_text(text)
        
        # Для першої частини вмикаємо прев'ю
        first_part = f"⚖️ **Результат (Ч. 1):**\n\n{parts[0]}"
        await _safe_send(first_part, is_edit=bool(status_msg), preview_opts=link_preview_cfg)
            
        # Для наступних частин вимикаємо прев'ю
        for i, part in enumerate(parts[1:], 2):
            await _safe_send(f"⚖️ **Результат (Ч. {i}):**\n\n{part}", is_edit=False, preview_opts=no_preview)

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
            # 🔥 NEW: обробка voice/audio
            if not raw_text and (msg.voice or msg.audio):
                status_msg = await msg.reply_text("🎤 Розпізнаю аудіо...")

                try:
                    file = await context.bot.get_file(
                        msg.voice.file_id if msg.voice else msg.audio.file_id
                    )

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
                        await file.download_to_drive(tmp.name)
                        wav_path = tmp.name.replace(".ogg", ".wav")
                        convert_to_wav(tmp.name, wav_path)
                        audio_path = wav_path

                    transcript = await transcribe_audio(audio_path)

                    raw_text = transcript

                    await status_msg.edit_text(
                        f"📝 Розпізнано:\n\n{transcript[:200]}..."
                    )

                except Exception as e:
                    await status_msg.edit_text(f"❌ Помилка розпізнавання: {str(e)}")
                    return
            
            # 1в. Обробка відео (звичайне відео або кружечок)
            if not raw_text and (msg.video or msg.video_note):
                status_msg = await msg.reply_text("📥 Завантажую відео для аналізу...")
                try:
                    video_file = await context.bot.get_file(
                        msg.video.file_id if msg.video else msg.video_note.file_id
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                        await video_file.download_to_drive(tmp.name)
                        video_path = tmp.name
                    
                    await status_msg.edit_text("🎥 Аналізую відео за допомогою спеціальної моделі (Gemma 3)...")
                    video_analysis = await analyze_video_with_together(video_path)
                    
                    if "Помилка" in video_analysis:
                        await status_msg.edit_text(f"❌ {video_analysis}")
                        user_states[uid]["action"] = None
                        return

                    await status_msg.edit_text("🧠 Виділяю ключові факти для пошуку...")
                    factors = await extract_factors_from_video_analysis(video_analysis)
                    
                    if not factors or "NO_FACTUAL_CONTENT" in factors:
                        await status_msg.edit_text("❌ Це відео не містить фактичної інформації для перевірки (можливо, це розважальний контент або меми).")
                        user_states[uid]["action"] = None
                        return
                    
                    raw_text = factors
                    user_states[uid]["video_analysis"] = video_analysis
                    
                    await status_msg.edit_text(f"✅ Відео проаналізовано. Знайдені ключові заяви/події:\n\n_{factors}_", parse_mode="Markdown")

                except Exception as e:
                    await status_msg.edit_text(f"❌ Помилка обробки відео: {str(e)}")
                    return

            # 1б. Обробка зображень через Vision API
            if msg.photo and not raw_text.strip():
                # Фото без тексту/підпису — аналізуємо через GPT-4o-mini Vision
                vision_msg = await msg.reply_text("🖼️ Виявлено зображення. Аналізую вміст...")
                largest_photo = msg.photo[-1]  # Telegram дає список від малого до великого
                extracted = await extract_text_from_image(context.bot, largest_photo.file_id)
                if extracted:
                    raw_text = f"[Зображення] {extracted}"
                    await vision_msg.edit_text(
                        f"✅ Вміст зображення розпізнано:\n\n_{extracted[:200]}{'...' if len(extracted) > 200 else ''}_",
                        parse_mode="Markdown"
                    )
                else:
                    await vision_msg.edit_text(
                        "❌ Зображення не містить фактичної інформації для перевірки. "
                        "Надішліть скриншот із текстом або фото події."
                    )
                    user_states[uid]["action"] = None
                    return
            elif msg.photo and raw_text.strip():
                # Фото з підписом — також аналізуємо зображення й додаємо до тексту
                vision_msg = await msg.reply_text("🖼️ Аналізую зображення + підпис...")
                largest_photo = msg.photo[-1]
                extracted = await extract_text_from_image(context.bot, largest_photo.file_id)
                if extracted:
                    raw_text = f"{raw_text}\n\n[Вміст зображення]: {extracted}"
                await vision_msg.delete()
            
            if "threads.net" in raw_text or "threads.com" in raw_text:
                tmp_msg = await msg.reply_text("🌐 Виявлено посилання Threads. Перевіряю доступ до API...")
                threads_token = os.getenv("THREADS_ACCESS_TOKEN", "").strip(' "')
                threads_service = ThreadsService(threads_token)
                
                if not await threads_service.is_token_valid():
                    await tmp_msg.edit_text("❌ Помилка: Токен доступу Threads недійсний або прострочений.")
                    user_states[uid]["action"] = None
                    return
                
                await tmp_msg.edit_text("🌐 Отримую оригінальний текст поста через API...")
                post_data = await threads_service.get_post_data(raw_text)
                if post_data:
                    post_text = post_data.get("text")       # може бути None
                    post_image_url = post_data.get("image_url")

                    # Аналізуємо зображення якщо воно є (завжди)
                    img_description = None
                    if post_image_url:
                        await tmp_msg.edit_text("🖼️ Аналізую зображення поста...")
                        img_description = await analyze_image_from_url(post_image_url)

                    # Формуємо фінальний текст для аналізу
                    parts = []
                    if post_text:
                        parts.append(f"Отримано з Threads:\n{post_text}")
                    if img_description:
                        parts.append(f"[Зображення до поста]: {img_description}")

                    if parts:
                        raw_text = "\n\n".join(parts)
                        if post_text and img_description:
                            await tmp_msg.edit_text("✅ Текст + зображення поста з Threads завантажено.")
                        elif img_description:
                            await tmp_msg.edit_text("✅ Пост без тексту — проаналізовано зображення.")
                        else:
                            await tmp_msg.edit_text("✅ Інформація з поста Threads успішно завантажено.")
                    else:
                        await tmp_msg.edit_text("❌ Пост не містить ні тексту, ні інформативного зображення.")
                        user_states[uid]["action"] = None
                        return
                else:
                    await tmp_msg.edit_text("❌ Не вдалося отримати інформацію з поста Threads. Можливо, пост приватний або видалений.")
                    user_states[uid]["action"] = None
                    return

            
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
                logger.debug(f"Attempt 1 Query: {search_query}") # Для дебагу
                
                raw = await serper_search(search_query, os.getenv("SERPER_API_KEY"))
                
                # 2. УНІВЕРСАЛЬНИЙ FALLBACK:
                # Якщо результатів 0, значить запит був занадто розумним 
                # або події не існує.
                # Спробуємо знайти хоча б згадку джерела або ключових імен.
                if not raw:
                    logger.debug("Attempt 1 failed. Trying broad search...")
                    # Простий алгоритм: беремо перші 30 слів тексту, 
                    # щоб Google сам розібрався
                    fallback_query = claim.replace("\n", " ")[:200]
                    raw = await serper_search(
                        fallback_query, os.getenv("SERPER_API_KEY")
                    )

                verified, unverified = filter_sources(raw)
                video_analysis = state.get("video_analysis")
                res = await call_base_gpt(
                    claim, verified, unverified, os.getenv("MODEL_NAME"), uid, video_analysis
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
            logger.error(f"КРИТИЧНА ПОМИЛКА: {e}", exc_info=True)
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