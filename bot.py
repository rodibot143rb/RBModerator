import json
import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode  # Импортируем ParseMode из telegram.constants

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def sanitize_filename(name):
    # Заменяем недопустимые символы в имени файла
    return "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in name).rstrip()

async def log_message_to_file(chat_title, user_name, user_id, message_text, date):
    try:
        log_entry = {
            "name": user_name,
            "id": user_id,
            "message": message_text,
            "date": date.isoformat()
        }

        # Используем название чата для имени файла
        safe_chat_title = sanitize_filename(chat_title)
        file_name = f"{safe_chat_title}.json"

        if not os.path.isfile(file_name):
            with open(file_name, 'w') as file:
                json.dump([], file)

        with open(file_name, 'r') as file:
            data = json.load(file)

        data.append(log_entry)

        with open(file_name, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error logging message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        keyboard = [['Просмотреть все файлы', 'Стереть историю']]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start command: {e}")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем список всех файлов JSON в текущей директории
        files = [f for f in os.listdir() if f.endswith('.json')]

        if not files:
            await update.message.reply_text("Нет доступных файлов.")
            return

        # Создаем клавиатуру с кнопками для каждого файла, используя название чата
        keyboard = [[f.split('.json')[0]] for f in files]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text('Выберите чат для просмотра:', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error listing files: {e}")

async def view_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Получаем имя файла из текста кнопки
        chat_title = sanitize_filename(update.message.text)
        file_name = f"{chat_title}.json"

        logger.info(f"Attempting to open file: {file_name}")

        if not os.path.isfile(file_name):
            await update.message.reply_text("Файл не найден.")
            return

        with open(file_name, 'r') as file:
            data = json.load(file)

        if not data:
            await update.message.reply_text("Файл пуст.")
            return

        # Форматируем сообщения с использованием Markdown
        messages = "\n".join([f"**{entry['name']}** ({entry['id']}): **{entry['message']}** [{entry['date']}]" for entry in data])
        await update.message.reply_text(messages, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error viewing file: {e}")
        await update.message.reply_text("Произошла ошибка при открытии файла.")

async def clear_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Для простоты очистки истории удаляем все файлы chat_log.json
        files = [f for f in os.listdir() if f.endswith('.json')]

        for file in files:
            os.remove(file)

        await update.message.reply_text("История сообщений очищена.")
    except Exception as e:
        logger.error(f"Error clearing history: {e}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_title = update.effective_chat.title or f"Chat_{update.effective_chat.id}"
        user_name = update.effective_user.full_name
        user_id = update.effective_user.id
        message_text = update.message.text
        date = update.message.date

        if message_text == 'Просмотреть все файлы':
            await list_files(update, context)
        elif message_text == 'Стереть историю':
            await clear_history(update, context)
        elif any(fname.startswith(sanitize_filename(message_text)) for fname in os.listdir() if fname.endswith('.json')):
            await view_file(update, context)
        else:
            await log_message_to_file(chat_title, user_name, user_id, message_text, date)
    except Exception as e:
        logger.error(f"Error in message handler: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует ошибки, вызванные обновлениями Telegram API."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    # Используем ApplicationBuilder для создания приложения
    application = ApplicationBuilder().token("7974396954:AAFREMfQ3fpHGMKDXOL8ldER0uC0-O8LP04").build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
