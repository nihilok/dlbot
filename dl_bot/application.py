from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler

import logging

from telegram.ext.filters import TEXT

from dl_bot.commands import start, whitelist_user, whitelist_group, un_whitelist_user, un_whitelist_group, \
    url_list_message_handler
from dl_bot.settings import TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def build_and_run():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('add_user', whitelist_user))
    application.add_handler(CommandHandler('add_group', whitelist_group))
    application.add_handler(CommandHandler('remove_user', un_whitelist_user))
    application.add_handler(CommandHandler('remove_group', un_whitelist_group))
    application.add_handler(MessageHandler(TEXT, url_list_message_handler))
    application.run_polling()


if __name__ == "__main__":
    build_and_run()
