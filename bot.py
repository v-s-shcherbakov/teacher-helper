import asyncio
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import TELEGRAM_TOKEN
from data_handler import init_db, get_article_by_category
from api_perplexity import generate_task

# Включаем логи
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUBJECT, GRADE, TASK_DONE = range(3)

async def start(update, context):
    """Стартовая команда"""
    keyboard = [
        [InlineKeyboardButton("🌌 Космос", callback_data="space")],
        [InlineKeyboardButton("🦁 Животные", callback_data="animals")],
        [InlineKeyboardButton("🔬 Наука", callback_data="science")],
        [InlineKeyboardButton("🌍 Природа", callback_data="nature")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🧠 Выбери предмет для загадки:",
        reply_markup=reply_markup
    )
    return SUBJECT

async def subject(update, context):
    """Выбор предмета"""
    query = update.callback_query
    await query.answer()
    context.user_data['subject'] = query.data
    print(f"📚 Выбран предмет: {query.data}")
    
    # Кнопки классов
    keyboard = [
        [InlineKeyboardButton(f"{i} класс", callback_data=f"{query.data}_{i}") for i in range(2,6)],
        [InlineKeyboardButton(f"{i} класс", callback_data=f"{query.data}_{i}") for i in range(6,10)],
        [InlineKeyboardButton("10-11 класс", callback_data=f"{query.data}_11")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        f"📚 {query.data.title()} — выбери класс:",
        reply_markup=reply_markup
    )
    return GRADE

async def grade(update, context):
    """Выбор класса + генерация"""
    query = update.callback_query
    await query.answer()
    
    
    subject, grade = query.data.split('_')
    grade = int(grade)
    context.user_data['grade'] = grade
    
    print(f"🎯 {subject}, {grade} кл. Ищем статью...")
    
    # Берём статью
    article = get_article_by_category(subject, 1)
    if not article:
        await query.edit_message_text("❌ Нет статей. Запусти `python scraper.py`")
        return ConversationHandler.END
    
    print(f"📖 Статья найдена: {article['title'][:50]}")
    
    # Генерируем задачу
    task = generate_task(article, subject, grade)
    
    # Кнопки "Ещё/Сменить"
    keyboard = [
        [InlineKeyboardButton("➕ Ещё одну!", callback_data="more")],
        [InlineKeyboardButton("🔄 Сменить предмет", callback_data="new")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Показываем задачу
    message = f"""🧩 **Загадка для {grade} класса ({subject.title()})**

{task['task']}

*Ответ:* `{task['answer']}`

ℹ️ *Пояснение:* {task['explanation']}"""
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    return TASK_DONE

async def task_done(update, context):
    """Кнопки после задачи"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "more":
        # Повторяем с тем же предметом/классом
        subject = context.user_data.get('subject')
        grade = context.user_data.get('grade')
        if subject and grade:
            await grade(update, context)  # Ещё одну!
            return GRADE
        else:
            await query.edit_message_text("❌ Ошибка состояния")
    
    elif query.data == "new":
        # Назад к выбору предмета
        keyboard = [
            [InlineKeyboardButton("🌌 Космос", callback_data="space")],
            [InlineKeyboardButton("🦁 Животные", callback_data="animals")],
            [InlineKeyboardButton("🔬 Наука", callback_data="science")],
            [InlineKeyboardButton("🌍 Природа", callback_data="nature")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🧠 Выбери новый предмет:",
            reply_markup=reply_markup
        )
        return SUBJECT
    
    return TASK_DONE

async def cancel(update, context):
    """Отмена"""
    await update.callback_query.edit_message_text("👋 До свидания!")
    return ConversationHandler.END

def main():
    """Запуск бота"""
    init_db()  # Инициализация БД
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # ConversationHandler для полного flow
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SUBJECT: [CallbackQueryHandler(subject, pattern='^(space|animals|science|nature)$')],
            GRADE: [CallbackQueryHandler(grade, pattern='^(space|animals|science|nature)_(2|3|4|5|6|7|8|9|11)$')],
            TASK_DONE: [CallbackQueryHandler(task_done, pattern='^(more|new)$')]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
        allow_reentry=True
    )
    
    app.add_handler(conv_handler)
    print("🤖 Бот запущен! /start")
    app.run_polling(allowed_updates=['message', 'callback_query'])

if __name__ == '__main__':
    main()
