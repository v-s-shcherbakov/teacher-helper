# db_maintenance.py — УПРАВЛЕНИЕ БАЗОЙ
import sqlite3
from datetime import datetime, timedelta

def cleanup_old(days=90):
    """Удаляет старые статьи."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
    
    deleted = c.execute(
        'DELETE FROM articles WHERE scraped_at < ?', 
        (cutoff,)
    ).rowcount
    
    conn.commit()
    conn.close()
    print(f"🗑️  Удалено статей старше {days} дней: {deleted}")
    return deleted

def show_stats():
    """Статистика."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    
    total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    today = c.execute("SELECT COUNT(*) FROM articles WHERE DATE(scraped_at)=DATE('now')").fetchone()[0]
    
    print(f"📊 БАЗА: {total} всего | {today} сегодня")
    
    sources = c.execute("""
        SELECT source, COUNT(*), category 
        FROM articles GROUP BY source, category 
        ORDER BY COUNT(*) DESC LIMIT 10
    """).fetchall()
    
    print("🏆 ТОП:")
    for s, count, cat in sources:
        print(f"   {s:<20} {cat:<10} {count}")
    
    conn.close()

def vacuum_db():
    """Оптимизация БД."""
    conn = sqlite3.connect('riddles.db')
    conn.execute('VACUUM')
    conn.close()
    print("🔧 БД оптимизирована")

if __name__ == "__main__":
    print("🧹 УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ")
    cleanup_old(90)
    show_stats()
    vacuum_db()
