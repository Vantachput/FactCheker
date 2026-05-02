import aiohttp
import re
from utils.logger import logger

class ThreadsService:
    def __init__(self, token):
        self.token = token
        self.base_url = "https://graph.threads.net/v1.0"

    def extract_post_id(self, url: str) -> str:
        """Синхронна функція, бо регулярні вирази працюють миттєво"""
        pattern = r"threads\.(?:net|com)/@[^/]+/post/([^/?]+)"
        match = re.search(pattern, url)
        return match.group(1) if match else None

    def extract_author(self, url: str) -> str:
        """Витягує @username автора з URL поста Threads."""
        match = re.search(r"threads\.(?:net|com)/@([^/]+)/post/", url)
        return match.group(1) if match else None

    async def get_post_text(self, url: str) -> str:
        """Асинхронна функція для мережевого запиту"""
        post_id = self.extract_post_id(url)
        if not post_id:
            logger.error(f"Не вдалося витягнути ID з URL: {url}")
            return None

        # Якщо ID складається лише з цифр, це Media ID і Graph API запрацює
        if post_id.isdigit():
            params = {
                "fields": "text,username,timestamp",
                "access_token": self.token
            }
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/{post_id}", params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "text" in data:
                                username = data.get('username') or self.extract_author(url) or 'невідомий'
                                return f"Автор (@{username}):\n{data['text']}"
                            logger.warning(f"API Threads повернуло порожній текст: {data}")
                            return None
                        else:
                            error_data = await response.text()
                            logger.error(f"Помилка API Threads (Статус {response.status}): {error_data}")
                            return None
            except Exception as e:
                logger.error(f"Виняток при запиті до Threads API: {e}")

        # Якщо це літерний шорткод (напр. DXwLvGviJgD), Graph API поверне помилку 400.
        # Тому ми використовуємо скрапінг HTML мета-тегів, що не потребує токена.
        import html
        try:
            # Важливо: використовуємо простий User-Agent. Facebot блокується (429), 
            # а складний Chrome User-Agent повертає порожній React-додаток.
            headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        # Читаємо байти та декодуємо вручну, щоб уникнути
                        # помилок автоматичного визначення кодування aiohttp
                        raw = await response.read()
                        text = raw.decode('utf-8', errors='replace')
                        # re.DOTALL дозволяє матчити переноси рядків у тексті поста
                        m = re.search(r'property="og:description"\s+content="(.*?)"', text, re.DOTALL)
                        if m:
                            post_text = html.unescape(m.group(1))
                            # Витягуємо автора з URL і з og:title (якщо є)
                            author = self.extract_author(url)
                            title_m = re.search(r'property="og:title"\s+content="(.*?)"', text, re.DOTALL)
                            if title_m:
                                author_display = html.unescape(title_m.group(1))
                            else:
                                author_display = f"@{author}" if author else "невідомий"
                            return f"Автор ({author_display}):\n{post_text}"
                        
                        logger.warning(f"API Threads: не знайдено og:description на сторінці: {url}")
                        return None
                    else:
                        logger.error(f"Помилка завантаження сторінки Threads (Статус {response.status})")
                        return None
        except Exception as e:
            logger.error(f"Виняток при скрапінгу Threads: {e}")
            return None

    async def is_token_valid(self) -> bool:
        """Перевіряє, чи токен досі активний."""
        url = f"{self.base_url}/me"
        params = {
            "fields": "id,username",
            "access_token": self.token
        }
        
        try:
            logger.info(f"Checking token. Length: {len(self.token) if self.token else 0}, First 5: {self.token[:5] if self.token else 'None'}, Last 5: {self.token[-5:] if self.token else 'None'}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    # Якщо статус 200, токен працює
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Токен валідний для користувача: {data.get('username')}")
                        return True
                    else:
                        error_data = await response.json()
                        logger.error(f"Токен недійсний або прострочений: {error_data}")
                        return False
        except Exception as e:
            logger.error(f"Помилка під час перевірки токена: {e}")
            return False