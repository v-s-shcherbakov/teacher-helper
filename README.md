# Teacher Helper Bot

Telegram бот для учителей: научные загадки и факты для уроков.

Общее описание проекта
Проект — Telegram‑бот, который:
- парсит научно‑популярные статьи и сохраняет их в SQLite‑базу;
​- по запросу учителя (предмет + класс) генерирует познавательную задачку на основе статьи через Perplexity API (модель sonar‑pro);
- сохраняет сгенерированные задачи в отдельную таблицу для повторного использования.
​
Стек:
- Python 3.12+
- python-telegram-bot для работы с Telegram;
- requests для Perplexity API;
- sqlite3 для хранения статей и задач.
​
Файлы и их назначение
bot.py — логика Telegram‑бота
Отвечает за:
- запуск бота и регистрацию хендлеров команд и кнопок;
- диалог: выбор предмета → выбор класса → генерация задачки → кнопки «Ещё» и «Сменить предмет»;
- вызовы:
    - init_db() и функции из data_handler.py для работы с БД;
    ​- generate_task() из api_perplexity.py для генерации задач.
​
Ключевые моменты:
- использует ConversationHandler с состояниями SUBJECT, GRADE, TASK_DONE;
- кнопки:
    - предметы: space, animals, science, nature;
    - после задачи: more (ещё задачка по тому же предмету и классу), new (сменить предмет);
​- логи в терминал помогают отладить выбор статьи и генерацию.
​

api_perplexity.py — интеграция с Perplexity API
Отвечает за:
- формирование prompt’а на русском для генерации познавательной задачки на основе статьи (заголовок + summary);
- HTTP‑запрос к Perplexity (/chat/completions) через requests;
- разбор ответа, извлечение JSON‑структуры вида:

```python
json
{
  "task": "Текст задачи",
  "answer": "Краткий ответ",
  "explanation": "Короткое пояснение"
}
```

- retry и fallback:
    - при ошибках (400/401/429/timeout) несколько попыток;
    - если все неудачны — возвращает «заглушку»‑задачу, чтобы бот не падал.
​
Использует:
- PERPLEXITY_API_KEY из config.py / .env;
- модель sonar-pro, которую вы тестировали и она единственная стабильно работает на вашем ключе.
​

data_handler.py — база статей и задач
Эта часть проекта объединяет две функции: умную дедупликацию статей и хранение задач.
​

Основные блоки:
1. init_db()
    - создаёт таблицу articles с уникальностью пары (source, external_id) - защита от дублей при парсинге;
​    - создаёт таблицу tasks для сохранения сгенерированных задач (с полями article_id, category, grade_level, task_text, answer, explanation, used_count).
​
2. save_article(...)
    - вставляет новую статью;
    - при дубликате по (source, external_id) ловит IntegrityError и возвращает False.
​
3. cleanup_old_articles(days=30)
    - удаляет статьи старше заданного количества дней по полю scraped_at.
​
4. get_stats()
    - возвращает общее число статей, количество новых за сегодня и статистику по источникам.
​
5. get_article_by_category(bot_category, limit=1)
    - принимает код категории из бота (space, animals, science, nature);
    - использует маппинг bot_category → список ключевых слов по title/summary/content, чтобы находить статьи даже если категория в RSS другая (human, climate, biology и т.п.);
    - возвращает один словарь статьи {"id", "title", "summary", "content"} или None, если ничего не найдено.

6. save_task(article_id, category, grade_level, task_text, answer, explanation)
    - сохраняет сгенерированную задачку в таблицу tasks и возвращает её id;- позволяет позже повторно использовать уже готовые задачи.

7. get_random_task(category=None, grade_level=None)
    - даёт случайную задачу из таблицы tasks с опциональными фильтрами по категории и классу.
​

scraper.py и scraper_test.py — парсинг статей
Назначение:
- scraper.py — основной парсер RSS/страниц научпоп‑ресурсов:
    - вытягивает заголовок, url, summary, полный контент и «сырую» категорию;
    - нормализует категорию (например, space, physics, biology);
    - вызывает save_article(...), поэтому дубли не попадают в БД.
​
- scraper_test.py — вспомогательный скрипт для диагностики парсера и БД (показывает количество статей, категории и т.п.).
​
Запускаются вручную(python scraper.py) или по расписанию (cron/Task Scheduler), чтобы база статей регулярно пополнялась.
​
config.py и .env — конфигурация и секреты
Отвечают за:
- загрузку токенов:
    - TELEGRAM_TOKEN — токен телеграм‑бота;
    - PERPLEXITY_API_KEY — ключ Perplexity API;
​- в .env хранятся реальные значения (KEY=VALUE без кавычек и пробелов), config.py их читает;
​- когда были проблемы с загрузкой .env, вы временно хардкодили токен в config.py для отладки.
​

db_maintenance.py / database.py — обслуживание БД
(Названия могут отличаться, но по переписке функция одна.)
Назначение:
- вызов cleanup_old_articles() и get_stats() для регулярной чистки и мониторинга базы;
- может выводить количество удалённых записей и текущую статистику.
​

Зависимости проекта
Основные Python‑зависимости (используются во всех скриптах проекта):
​- python-telegram-bot==20.7 — Telegram API (Application, CommandHandler, CallbackQueryHandler, ConversationHandler).
- python-dotenv — загрузка переменных окружения из .env.
- requests — HTTP‑запросы к Perplexity API.
- feedparser, beautifulsoup4 (bs4) — парсинг RSS/HTML для scraper.py.
​- стандартная библиотека:
    - sqlite3 — база данных;
    - datetime — даты/сроки хранения статей;
    - json, re, time — обработка JSON‑ответов Perplexity, регулярки и retry‑задержки.
​

Пример requirements.txt для проекта:

```python
python-telegram-bot==20.7
python-dotenv==1.0.0
requests==2.31.0
feedparser
beautifulsoup4
```



Подсказки по работе с гитом
git add .
git commit -m "любое изменение"
git push origin main
git status                    # Что изменилось?
git add -A                    # Добавляем ВСЕ файлы к выгрузке в гит
git status                    # Green файлы?
git commit -m "feat: README + fuzzy data_handler"
git push origin main          # ✅
git branch                    # проверить название ветки
git branch -M main            # переименовать ветку в main
git rm --cached .env          # очистить env из проекта



Как всё работает вместе (кратко).
1. scraper.py → парсит источники, через save_article пополняет articles без дублей.
​2. Учитель в Telegram /start → bot.py запускает диалог (предмет → класс).
​3. bot.py берёт статью из get_article_by_category(...) в data_handler.py.
​4. api_perplexity.py по статье и параметрам вызывает Perplexity (sonar‑pro) и возвращает задачу.
​5. bot.py показывает задачу, сохраняет её через save_task(...), предлагает «Ещё» или «Сменить предмет».
​

## 🚀 Быстрый старт