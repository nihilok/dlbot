import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes
from telegram.ext.filters import TEXT

from dl_bot.commands import start, download_url_list, PATH, whitelist_user, whitelist_group
from dl_bot.auth_helpers import get_users
from dl_bot.file_operations import split_large_file, get_new_files
from dl_bot.settings import TOKEN
from dl_bot.yt_funcs import set_tags


class DlBot:

    def __init__(self):
        self.application = ApplicationBuilder().token(TOKEN)
        self.users = get_users()

    def build_and_run(self):
        application = self.application.build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('add_user', whitelist_user))
        application.add_handler(CommandHandler('add_group', whitelist_group))
        application.add_handler(MessageHandler(TEXT, self.url_list_message_handler))
        application.run_polling()

    async def check_auth(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id in self.users["chats"]:
            return True
        if (user_id := update.effective_user.id) not in self.users['users']:
            if user_id != self.users['superuser']:
                await context.bot.send_message(update.effective_chat.id, "Sorry this bot is restricted")
                return False
        return True

    async def url_list_message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await self.check_auth(update, context) is False:
            return
        async for mp3, artist, title in download_url_list(update.message.text):
            full_path = PATH / mp3
            if split_large_file(full_path) is False:
                files = [full_path]
            else:
                files = [file for file in get_new_files()]
                os.remove(full_path)
            for file in files:
                await set_tags(file, title, artist)
                with open(file, 'rb') as f:
                    await context.bot.send_audio(update.effective_chat.id, f)
                os.remove(file)
