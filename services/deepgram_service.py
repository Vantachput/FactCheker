import aiohttp
import asyncio
import os
from utils.logger import logger


DEEPGRAM_URL = "https://api.deepgram.com/v1/listen"


class DeepgramError(Exception):
    pass


async def transcribe_audio(file_path: str) -> str:
    """
    Транскрибує аудіо через Deepgram (nova-3, multilingual)
    """

    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise DeepgramError("DEEPGRAM_API_KEY not found in .env")

    params = {
        "model": "nova-3",
        "smart_format": "true",
        "punctuate": "true",
        "detect_language": "true",   # 🔥 ключове для тебе
    }

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "audio/wav",
    }

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            with open(file_path, "rb") as f:
                audio_data = f.read()

            async with session.post(
                DEEPGRAM_URL,
                params=params,
                headers=headers,
                data=audio_data
            ) as resp:

                if resp.status != 200:
                    text = await resp.text()
                    raise DeepgramError(f"Deepgram API error: {resp.status} - {text}")

                data = await resp.json()

                transcript = (
                    data.get("results", {})
                        .get("channels", [{}])[0]
                        .get("alternatives", [{}])[0]
                        .get("transcript", "")
                )

                if not transcript:
                    raise DeepgramError("Empty transcription")

                return transcript

    except asyncio.TimeoutError:
        raise DeepgramError("Deepgram request timeout")

    except Exception as e:
        logger.error(f"Deepgram error: {e}", exc_info=True)
        raise