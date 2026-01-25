import re
from datetime import datetime
import pytz

def split_text(text, max_length=4000):
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

def get_progress_bar(text):
    match = re.search(r'(\d+)%', text)
    if match:
        percent = int(match.group(1))
        filled = int(percent / 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)
        return f"\n\n📊 Шкала впевненості ШІ:\n{bar} {percent}%"
    return ""

def escape_markdown(text):
    if not text:
        return ""
    parse_fix = text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[")
    return parse_fix

def get_ukraine_time():
    tz_ua = pytz.timezone('Europe/Kyiv')
    now_ua = datetime.now(tz_ua)
    return now_ua.strftime("%d.%m.%Y %H:%M")