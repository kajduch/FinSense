import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROXY_BASE_URL = os.getenv("PROXY_BASE_URL", "https://ai.starimg.ru/v1/chat/completions")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in .env")
