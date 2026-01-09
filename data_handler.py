# data_handler.py — Полная версия с ДЕДУПЛИКАЦИЕЙ + FUZZY ПОИСК
import sqlite3
from datetime import datetime, timedelta

def init_db():
    """Инициализация БД: статьи + задачи"""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    
    # Статьи (с дедуликацией)
    c.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            external_id TEXT,
            title TEXT, url TEXT, summary TEXT, content TEXT,
            category TEXT, published_at TEXT, scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source, external_id)
        )
    """)
    
    # Задачи (с кэшем)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER,
            category TEXT,        -- space, animals, physics...
            grade_level INTEGER,  -- 1-11 класс
            task_text TEXT,       -- текст задачки
            answer TEXT,          -- правильный ответ
            explanation TEXT,     -- развернутое пояснение
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            used_count INTEGER DEFAULT 0,
            FOREIGN KEY(article_id) REFERENCES articles(id)
        )
    """)
    
    conn.commit()
    conn.close()

def save_article(source, external_id, title, url, summary, content, category, published_at):
    """Сохраняет с проверкой дубликатов (БЕЗ ПОТЕРИ)."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    
    try:
        c.execute("""
            INSERT INTO articles 
            (source, external_id, title, url, summary, content, category, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (source, external_id, title, url, summary, content, category, published_at))
        
        if c.rowcount > 0:
            conn.commit()
            conn.close()
            return True  # новая статья
        else:
            conn.close()
            return False  # дубликат
    except sqlite3.IntegrityError:
        conn.close()
        return False

def cleanup_old_articles(days=30):
    """Удаляет статьи старше N дней."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    deleted = c.execute(
        "DELETE FROM articles WHERE scraped_at < ?", 
        (cutoff,)
    ).rowcount
    
    conn.commit()
    conn.close()
    return deleted

def get_stats():
    """Статистика."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    
    total = c.execute('SELECT COUNT(*) FROM articles').fetchone()[0]
    new_today = c.execute("""
        SELECT COUNT(*) FROM articles 
        WHERE DATE(scraped_at) = DATE('now')
    """).fetchone()[0]
    
    sources = c.execute("""
        SELECT source, COUNT(*) FROM articles 
        GROUP BY source ORDER BY COUNT(*) DESC LIMIT 10
    """).fetchall()
    
    conn.close()
    return total, new_today, sources

# 🆕 FUZZY ПОИСК ПО КНОПКАМ БОТА
def get_article_by_category(bot_category, limit=1):
    """Ищет статью по кнопке бота (space→космос, animals→животные)."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    
    # 🗺️ Маппинг кнопок → ключевые слова в статьях
    category_map = {
        'space':    ['космос', 'звезда', 'планета', 'астроном', 'space', 'galaxy', 'уfo'],
        'animals':  ['животн', 'птиц', 'рыб', 'млекопита', 'animals', 'biology', 'human'],
        'science':  ['физика', 'химия', 'наука', 'science', 'physic', 'математик'],
        'nature':   ['природа', 'растен', 'эколог', 'climate', 'earth', 'biology']
    }
    
    terms = category_map.get(bot_category, [bot_category.lower()])
    conditions = []
    params = []
    
    for term in terms:
        conditions.append("(LOWER(title) LIKE ? OR LOWER(summary) LIKE ? OR LOWER(content) LIKE ?)")
        params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
    
    if not conditions:
        conn.close()
        return None
    
    query = f"""
        SELECT id, title, summary, content 
        FROM articles 
        WHERE {' OR '.join(conditions)}
        ORDER BY scraped_at DESC 
        LIMIT ?
    """
    params.append(limit)
    
    c.execute(query, params)
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "title": result[1],
            "summary": result[2] or "",
            "content": result[3] or ""
        }
    return None

def save_task(article_id, category, grade_level, task_text, answer, explanation):
    """Сохраняет задачу (БЕЗ ИЗМЕНЕНИЙ)."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO tasks (article_id, category, grade_level, task_text, answer, explanation)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (article_id, category, grade_level, task_text, answer, explanation))
    task_id = c.lastrowid
    conn.commit()
    conn.close()
    return task_id

def get_random_task(category=None, grade_level=None):
    """Случайная задача (БЕЗ ИЗМЕНЕНИЙ)."""
    conn = sqlite3.connect('riddles.db')
    c = conn.cursor()
    
    query = "SELECT * FROM tasks"
    params = []
    
    if category:
        query += " WHERE LOWER(category) LIKE LOWER(?)"
        params.append(f"%{category}%")
    if grade_level:
        query += " AND grade_level = ?" if params else " WHERE grade_level = ?"
        params.append(grade_level)
    
    query += " ORDER BY RANDOM() LIMIT 1"
    
    task = c.execute(query, params).fetchone()
    conn.close()
    return task
