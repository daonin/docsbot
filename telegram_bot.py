import logging
import requests
import yaml
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
TELEGRAM_TOKEN = config['telegram_token']
API_URL = 'http://localhost:8000/ask'

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Задай вопрос по документации.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    try:
        resp = requests.post(API_URL, json={'question': question}, timeout=60)
        resp.raise_for_status()
        answer = resp.json().get('answer', 'Нет ответа.')
    except Exception as e:
        answer = f'Ошибка запроса: {e}'
    await update.message.reply_text(answer)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main() 