import requests
import json
import time
import re
from config import PERPLEXITY_API_KEY

def generate_task(article, category, grade_level, max_retries=2):
    """
    Генерирует образовательную задачу на основе статьи.
    Использует Perplexity sonar-pro с retry и fallback.
    """
    print(f"🔍 Генерация для '{category}', {grade_level} кл.")
    print(f"   Статья: '{article.get('title', 'Нет')[:60]}...'")
    
    for attempt in range(max_retries):
        try:
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Компактный prompt для стабильного JSON
            article_text = f"{article.get('title', '')}\n{article.get('summary', '')[:500]}"
            prompt = f"""Создай задачу для {grade_level} класса по теме "{category}".

Источник: {article_text}

Требования:
- Логическая задача (не просто факт)
- Для школьников {grade_level} кл.
- Русский язык
- Загадка учит новому факту
- Формат: "Что/Как/Почему...?" 
- Дети думают 1-2 мин

Верни ТОЛЬКО валидный JSON:
{{
  "task": "Текст задачи с вопросом?",
  "answer": "Краткий точный ответ",
  "explanation": "Пояснение 1-2 предложения"
}}"""

            payload = {
                "model": "sonar-pro",  # ✅ Ваша рабочая Pro-модель
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
                "temperature": 0.5,
                "stream": False
            }
            
            print(f"📡 Попытка {attempt+1}/2...")
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            print(f"   Статус: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"].strip()
                print(f"📄 Ответ (первые 100 симв.): {content[:100]}...")
                
                # Надёжный парсинг JSON
                json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                if json_match:
                    task_json = json.loads(json_match.group())
                    print("✅ JSON распарсен!")
                    return task_json
                else:
                    print("⚠️ JSON не найден, fallback парсинг")
                    # Извлекаем ключевые части
                    task_json = {
                        "task": content[:200] + "...?",
                        "answer": "См. пояснение",
                        "explanation": content[-150:] if len(content) > 150 else content
                    }
                    return task_json
                    
            elif resp.status_code == 429:  # Rate limit
                wait = 2 ** attempt
                print(f"⏳ Rate limit, ждём {wait}с")
                time.sleep(wait)
                continue
            else:
                print(f"❌ API: {resp.status_code} - {resp.text[:150]}")
                raise ValueError(f"API error: {resp.status_code}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON ошибка: {e}")
        except requests.exceptions.Timeout:
            print("⏰ Таймаут")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    # Graceful fallback
    print("🔄 Возвращаем заглушку")
    return {
        "task": f"Что вы знаете о {category}?",
        "answer": f"Тема из статьи '{article.get('title', 'Нет заголовка')[:30]}...'",
        "explanation": f"API временно недоступен. Запустите 'python scraper.py' для новых статей. Класс: {grade_level}"
    }

# Тест функции
if __name__ == "__main__":
    test_article = {"title": "Открытие новой планеты", "summary": "Астрономы нашли экзопланету в 100 световых годах."}
    result = generate_task(test_article, "space", 5)
    print("\n🧪 ТЕСТ РЕЗУЛЬТАТА:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
