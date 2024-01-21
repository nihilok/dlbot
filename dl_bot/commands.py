import datetime
import os
import time
from pathlib import Path

from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import ContextTypes

from dl_bot.auth_helpers import (
    add_group,
    add_user,
    check_auth,
    remove_group,
    remove_user,
    require_superuser,
)
from dl_bot.file_operations import get_new_files, split_large_file
from dl_bot.yt_funcs import download_url_list, set_tags

PATH = Path(os.path.dirname(os.path.dirname(__file__)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("visitors.csv", "a") as f:
        f.write(
            f"{update.effective_user.id},"
            f"{update.effective_user.username},"
            f"{update.effective_chat.id},"
            f"{datetime.datetime.now().isoformat()},\n"
        )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="dlbot at your service, boop beep!"
    )


async def url_list_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_auth(update) is False:
        return

    async def send_message(message: str):
        await context.bot.send_message(update.effective_chat.id, message)

    async for track in download_url_list(update.message.text, send_message):
        if isinstance(track, str):
            continue
        mp3, artist, title, url = track
        full_path = PATH / mp3
        if split_large_file(full_path) is False:
            files = [full_path]
        else:
            files = [file for file in get_new_files()]
            os.remove(full_path)
        for file in files:
            await set_tags(file, title, artist)
            if not os.path.getsize(file):
                os.remove(file)
                await send_message(f"Something went wrong downloading/extracting {mp3} from {url}")
                continue
            with open(file, "rb") as f:
                for i in range(3):
                    try:
                        await context.bot.send_audio(update.effective_chat.id, f)
                        break
                    except TimedOut:
                        break
                    except NetworkError as e:
                        await send_message(f"Something went wrong sending {mp3} to Telegram: {e}\n\nOriginal URL: {url}")
                        if i < 2:
                            time.sleep(5)
                            await send_message(
                                f"Retrying {i+1} of 2 times...")
            os.remove(file)


@require_superuser
async def whitelist_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    await add_group(group_id)
    await context.bot.send_message(group_id, f"Group whitelisted: {group_id}")


@require_superuser
async def whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        user_name = user.name
        await add_user(user_id)
        await context.bot.send_message(
            update.effective_chat.id, f"{user_name} whitelisted"
        )
    except AttributeError:
        await context.bot.send_message(
            update.effective_chat.id, "You must reply to a message to use this command."
        )


@require_superuser
async def un_whitelist_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    await remove_group(group_id)
    await context.bot.send_message(
        group_id, f"Group removed from whitelist: {group_id}"
    )


@require_superuser
async def un_whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        user_name = user.name
        await remove_user(user_id)
        await context.bot.send_message(
            update.effective_chat.id, f"{user_name} removed from whitelist"
        )
    except AttributeError:
        await context.bot.send_message(
            update.effective_chat.id, "You must reply to a message to use this command."
        )
