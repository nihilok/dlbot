import datetime
import os
import re
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from dl_bot.auth_helpers import require_superuser, add_group_to_file, add_user_to_file
from dl_bot.yt_funcs import download_single_url

PATH = Path(os.path.dirname(os.path.dirname(__file__)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("visitors.csv", 'a') as f:
        f.write(f'{update.effective_user.id},{update.effective_user.username},{update.effective_chat.id},{datetime.datetime.now().isoformat()},\n')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="dlbot at your service, boop beep!")


async def parse_message_for_urls(message):
    urls = re.findall(r'https://\S+', message)
    for url in urls:
        yield url


async def download_url_list(message):
    async for url in parse_message_for_urls(message):
        filename, artist, title, exit_code = await download_single_url(url)
        if not exit_code:
            yield filename, artist, title


@require_superuser
async def whitelist_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    await add_group_to_file(group_id)
    await context.bot.send_message(group_id, f"Group whitelisted: ({group_id})")


@require_superuser
async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.message.reply_to_message.from_user.id
        await add_user_to_file(user_id)
        await context.bot.send_message(update.effective_chat.id, f"User whitelisted: ({user_id})")
    except AttributeError:
        await context.bot.send_message(
            update.effective_chat.id,
            "You must reply to a message to user this command."
        )

