import datetime
import json
import os
import re
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from dl_bot.yt_funcs import download_single_url

PATH = Path(os.path.dirname(os.path.dirname(__file__)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("visitors.csv", 'a') as f:
        f.write(f'{update.effective_user.id},{update.effective_user.username},{update.effective_chat.id},{datetime.datetime.now().isoformat()},\n')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="dlbot at your service, boop beep!")


def get_users():
    with open('dl_bot/users.json', 'r') as f:
        try:
            return json.load(f)
        except FileNotFoundError as e:
            print(e)
            with open('dl_bot/users.json', 'w') as g:
                json.dump({"superuser": 0, "users": [], "chats": []}, g)
            return get_users()


async def parse_message_for_urls(message):
    urls = re.findall(r'https://\S+', message)
    for url in urls:
        yield url


async def download_url_list(message):
    async for url in parse_message_for_urls(message):
        filename, artist, title, exit_code = await download_single_url(url)
        if not exit_code:
            yield filename, artist, title
