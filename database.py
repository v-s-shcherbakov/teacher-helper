import sqlite3
import json
from pathlib import Path

class RiddleDB:
    def __init__(self, db_path="data/riddles.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS riddles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT UNIQUE NOT NULL,
                    answer TEXT NOT NULL,
                    source TEXT,
                    difficulty INTEGER DEFAULT 1,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def add_riddle(self, question, answer, source="", difficulty=1, category=""):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR IGNORE INTO riddles 
                    (question, answer, source, difficulty, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (question, answer, source, difficulty, category))
                conn.commit()
                return True
        except:
            return False
    
    def get_random_riddle(self, category=None):
        query = "SELECT question, answer FROM riddles"
        params = []
        if category:
            query += " WHERE category=?"
            params.append(category)
        query += " ORDER BY RANDOM() LIMIT 1"
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(query, params).fetchone()
            return dict(question=result[0], answer=result[1]) if result else None
    
    def count(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM riddles").fetchone()[0]
    
    def export_json(self):
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM riddles").fetchall()
        return [{"id": r[0], "question": r[1], "answer": r[2], "source": r[3]} for r in rows]
