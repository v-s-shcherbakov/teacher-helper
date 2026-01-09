import os
from dotenv import load_dotenv

load_dotenv()
print("🔍 Загружаем .env...")
#print(f"DEBUG: Telegram token: {'OK' if TELEGRAM_TOKEN else 'MISSING'}")
#print(f"DEBUG: Perplexity key: {'OK' if PERPLEXITY_API_KEY else 'MISSING'}")
#print("Файлы в папке:", os.listdir("."))
#print("Есть .env?", ".env" in os.listdir("."))
#print("TOKEN загружен?", bool(TELEGRAM_TOKEN))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

print("Файлы в папке:", [f for f in os.listdir(".") if f.endswith(('.py', '.env'))])
print("TELEGRAM_TOKEN:", "OK" if TELEGRAM_TOKEN else "❌ ПУСТО!")
print("PERPLEXITY_API_KEY:", "OK" if PERPLEXITY_API_KEY else "❌ ПУСТО!")


SOURCES = [
    "Science News Explores",
    "National Geographic Kids",
    "Science Journal for Kids",
    "Science Kids"
]

PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
