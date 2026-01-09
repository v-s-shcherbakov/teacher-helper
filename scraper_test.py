# scraper.py
import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
from urllib.parse import urljoin, urlparse
from data_handler import save_article
from config import SOURCES

def parse_sunnyfeed():
    """Парсит SunnyFeed News — главный источник."""
    print("📰 Парсим SunnyFeed...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Главная страница — ищем статьи
        resp = requests.get("https://www.sunnyfeednews.com", headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = []
        
        # SunnyFeed использует SPA, ищем data attributes или JSON в скриптах
        # Вариант 1: статьи в article/list-item блоках
        items = soup.find_all(['article', 'div'], class_=lambda x: x and any(kw in x.lower() for kw in ['post', 'news', 'article', 'item']))
        
        if not items:
            # Вариант 2: JSON в <script> тегах
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = script.string
                    if data and ('headline' in data or 'article' in data):
                        print(f"📄 Нашли JSON-LD: {data[:100]}...")
                        # TODO: парсинг JSON-LD
                except:
                    continue
        
        # ВРЕМЕННЫЙ РЕЗУЛЬТАТ для тестирования (замените на реальный парсинг)
        demo_articles = [
            {
                "external_id": "sunnyfeed_20260107_1",
                "title": "Звёзды мерцают из-за атмосферы Земли",
                "url": "https://www.sunnyfeednews.com/stars-twinkle",
                "summary": "Атмосфера преломляет свет звёзд, создавая эффект мерцания.",
                "content": "Звёзды кажутся мерцающими из-за турбулентности в земной атмосфере...",
                "category": "space",
                "published_at": "2026-01-07"
            },
            {
                "external_id": "sunnyfeed_20260107_2", 
                "title": "Киты поют песни длиной до 20 минут",
                "url": "https://www.sunnyfeednews.com/whales-sing",
                "summary": "Горбатые киты используют сложные песни для общения.",
                "content": "Самцы горбатых китов поют песни, которые могут длиться до 20 минут...",
                "category": "animals", 
                "published_at": "2026-01-07"
            }
        ]
        
        for art in demo_articles:
            save_article("sunnyfeed", **art)
            articles.append(art)
            
        print(f"✅ SunnyFeed: сохранено {len(articles)} статей")
        return articles
        
    except Exception as e:
        print(f"❌ SunnyFeed ошибка: {e}")
        return []

def run_scrapers():
    """Запускает все скрапперы."""
    from data_handler import init_db
    
    print("🚜 === ЕЖЕДНЕВНЫЙ ПАРСИНГ ===")
    init_db()
    
    # SunnyFeed — основной
    sunny_articles = parse_sunnyfeed()
    
    # TODO: добавить остальные SOURCES из config.py
    print(f"📊 ИТОГО: {len(sunny_articles)} статей в БД")
    
    # Проверяем БД
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM articles")
    count = c.fetchone()[0]
    conn.close()
    
    print(f"✅ В БД всего статей: {count}")
    print("🎉 Парсинг завершён!")

if __name__ == "__main__":
    run_scrapers()
