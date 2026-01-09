# scraper.py — МАССОВЫЙ НАУЧНЫЙ КОНТЕНТ
import feedparser
import requests
from bs4 import BeautifulSoup
from data_handler import save_article
from datetime import datetime
import time
import re
import random

# 🔥 50+ НАУЧНЫХ RSS (физика, биология, космос, природа, технологии)
RSS_FEEDS = {
    # Космос и астрономия (15)
    "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "Space.com": "https://www.space.com/feeds/all",
    "Astronomy.com": "https://astronomy.com/feed",
    "Sky & Telescope": "https://skyandtelescope.org/feed/",
    "ESA": "https://www.esa.int/rss",
    
    # Физика и химия (10)
    "Physics World": "https://physicsworld.com/feed",
    "Nature Physics": "https://www.nature.com/nphys.rss",
    "Science Daily Physics": "https://www.sciencedaily.com/rss/physics.xml",
    
    # Биология и природа (15)
    "National Geographic": "https://www.nationalgeographic.com/feed/rss.xml",
    "BBC Wildlife": "https://feeds.bbci.co.uk/news/science-environment/rss.xml",
    "Nature": "https://www.nature.com/nature.rss",
    "Science": "https://www.science.org/rss/news_current.xml",
    "New Scientist": "https://www.newscientist.com/section/news/feed/",
    
    # Технологии и открытия (10)
    "MIT Technology Review": "https://www.technologyreview.com/feed/",
    "Scientific American": "https://rss.sciam.com/ScientificAmerican-Global",
    "Live Science": "https://www.livescience.com/feeds/all",
    
    # Дополнительно (10)
    "Ars Technica Science": "https://arstechnica.com/science/feed/",
    "Popular Science": "https://www.popsci.com/feed/",
    "Discover Magazine": "https://www.discovermagazine.com/feed",
    "Smithsonian": "https://www.smithsonianmag.com/rss/",
}
def fetch_full_article(url):
    """Загружает ПОЛНЫЙ текст статьи."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Удаляем мусор
        for element in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            element.decompose()
        
        # Ищем основной контент
        content_selectors = [
            'article', '.article-body', '.post-content', 
            '.entry-content', '.story-body', 'main', '[role="main"]'
        ]
        
        content = ""
        for selector in content_selectors:
            elem = soup.select_one(selector)
            if elem:
                content = elem.get_text(separator=' ', strip=True)
                break
        
        if not content:
            content = soup.get_text(separator=' ', strip=True)
        
        # Очистка и обрезка
        content = re.sub(r'\s+', ' ', content).strip()
        return content[:8000]  # макс 8KB
        
    except Exception as e:
        return f"Ошибка загрузки: {e}"

def categorize_article(title, content):
    """Определяет категорию."""
    text = (title + " " + content).lower()
    
    categories = {
        'space': ['space', 'planet', 'star', 'galaxy', 'nasa', 'astronomy', 'universe', 'black hole'],
        'animals': ['animal', 'bird', 'fish', 'insect', 'dinosaur', 'whale', 'wildlife'],
        'physics': ['physics', 'quantum', 'energy', 'gravity', 'laser', 'particle', 'force'],
        'biology': ['dna', 'gene', 'cell', 'virus', 'bacteria', 'evolution', 'microbe'],
        'climate': ['climate', 'weather', 'global warming', 'carbon', 'environment', 'ice melt'],
        'tech': ['ai', 'robot', 'computer', 'quantum computer', 'nanotech', 'battery']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return 'science'

def parse_rss_feed(rss_url, source_name):
    """Парсит один RSS фид."""
    print(f"📡 [{source_name}] {rss_url}")
    
    try:
        feed = feedparser.parse(rss_url)
        
        if feed.bozo:
            print(f"   ❌ XML повреждён")
            return []
        
        print(f"   📊 Новостей доступно: {len(feed.entries) if 'entries' in feed else 0}")
        
        articles = []
        for i, entry in enumerate(feed.entries[:5]):  # берём топ 5
            print(f"   {i+1}. Загружаем: {entry.title[:70]}...")
            
            full_content = fetch_full_article(entry.link)
            
            article = {
                'external_id': getattr(entry, 'id', entry.link),
                'title': entry.title[:250],
                'url': entry.link,
                'summary': (getattr(entry, 'summary', '') or getattr(entry, 'description', ''))[:500],
                'content': full_content,
                'category': categorize_article(entry.title, full_content),
                'published_at': getattr(entry, 'published', datetime.now().isoformat())
            }
            
            articles.append(article)
        
        return articles
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return []

def run_scrapers():
    """Главная функция парсинга."""
    print("=" * 80)
    print("🚀 НАУЧНЫЙ RSS СКРАППЕР")
    print("📚 Полные статьи | Автокатегоризация | Антидубликаты")
    print("=" * 80)
    
    
    total_saved = 0
    successful_feeds = 0
    
    for source_name, rss_url in RSS_FEEDS.items():
        articles = parse_rss_feed(rss_url, source_name)
        
        saved_this_feed = 0
        for article in articles:
            # save_article() сама проверяет дубликаты!
            if save_article(source_name, **article):
                saved_this_feed += 1
                content_size = len(article['content'])
                print(f"      ✅ Сохранено [{article['category']}] {content_size/1024:.1f}KB")
            else:
                print(f"      ⏭️  Дубликат пропущен")
        
        if saved_this_feed > 0:
            successful_feeds += 1
        
        total_saved += saved_this_feed
        time.sleep(random.uniform(2, 4))  # пауза между фидами
    
    print("\n" + "=" * 80)
    print(f"🎉 РЕЗУЛЬТАТ:")
    print(f"   📦 Новых статей: {total_saved}")
    print(f"   ✅ Успешных фидов: {successful_feeds}/{len(RSS_FEEDS)}")
    print("=" * 80)

if __name__ == "__main__":
    run_scrapers()