import os
import re
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes

from yt_funcs import download_single_url


PATH = Path(os.path.dirname(os.path.dirname(__file__)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="dlbot at your service, boop beep!")


async def parse_message_for_urls(message):
    urls = re.findall(r'https://\S+', message)
    for url in urls:
        yield url


async def download_url_list(message):
    async for url in parse_message_for_urls(message):
        filename, exit_code = await download_single_url(url)
        if not exit_code:
            yield filename


async def url_list_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async for mp3 in download_url_list(update.message.text):
        full_path = PATH / mp3
        with open(full_path, 'rb') as f:
            await context.bot.send_audio(update.effective_chat.id, f)
        os.remove(full_path)
