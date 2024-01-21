import datetime
import os
import random
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
MAX_RETRIES = 3
RETRY_DELAY = 10


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

    # Keep track of sent error message IDs, so we can delete them if retries are successful.
    error_message_ids = []

    async def send_message(message: str):
        sent = await context.bot.send_message(update.effective_chat.id, message)
        return sent.message_id

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
                await send_message(f"Something went wrong downloading/extracting {mp3} from {url} (filesize was 0)")
                continue

            encountered_network_error = ""
            retried = 0
            for i in range(MAX_RETRIES):
                retried = i
                try:
                    with open(file, "rb") as f:
                        await context.bot.send_audio(update.effective_chat.id, f)
                    break
                except TimedOut:
                    break
                except Exception as e:
                    if not encountered_network_error == str(e):
                        sent_id = await send_message(f"Something went wrong sending {mp3} to Telegram: {e}")
                        error_message_ids.append(sent_id)
                        encountered_network_error = str(e)
                    if i < MAX_RETRIES - 1:
                        sent_id = await send_message(
                            f"Waiting {RETRY_DELAY} seconds and retrying ({i + 1} of {MAX_RETRIES} times)")
                        time.sleep(RETRY_DELAY)
                        error_message_ids.append(sent_id)
                    else:
                        await send_message(f"Failed to send track. Url: {url}")

            if retried < MAX_RETRIES - 1:
                for message_id in error_message_ids:
                    await context.bot.delete_message(update.effective_chat.id, message_id)

        for file in files:
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
