from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT
from commands import start, url_list_message_handler
from settings import TOKEN

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(TEXT, url_list_message_handler))
    application.run_polling()
