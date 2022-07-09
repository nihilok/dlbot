from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler
from telegram.ext.filters import TEXT
from dl_bot.commands import start, url_list_message_handler
from dl_bot.settings import TOKEN

import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
application = ApplicationBuilder().token(TOKEN)


def build_and_run():
    global application
    application = application.build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(TEXT, url_list_message_handler))
    application.run_polling()


if __name__ == "__main__":
    build_and_run()
