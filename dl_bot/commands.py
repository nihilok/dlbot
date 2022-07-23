import datetime
import os
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from dl_bot.auth_helpers import require_superuser, add_group, add_user, remove_group, \
    remove_user, check_auth
from dl_bot.file_operations import split_large_file, get_new_files
from dl_bot.yt_funcs import set_tags, download_url_list

PATH = Path(os.path.dirname(os.path.dirname(__file__)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("visitors.csv", 'a') as f:
        f.write(f'{update.effective_user.id},{update.effective_user.username},{update.effective_chat.id},{datetime.datetime.now().isoformat()},\n')
    await context.bot.send_message(chat_id=update.effective_chat.id, text="dlbot at your service, boop beep!")


async def url_list_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await check_auth(update) is False:
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
        await context.bot.send_message(update.effective_chat.id, f"{user_name} whitelisted")
    except AttributeError:
        await context.bot.send_message(
            update.effective_chat.id,
            "You must reply to a message to use this command."
        )


@require_superuser
async def un_whitelist_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    await remove_group(group_id)
    await context.bot.send_message(group_id, f"Group removed from whitelist: {group_id}")


@require_superuser
async def un_whitelist_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.message.reply_to_message.from_user
        user_id = user.id
        user_name = user.name
        await remove_user(user_id)
        await context.bot.send_message(update.effective_chat.id, f"{user_name} removed from whitelist")
    except AttributeError:
        await context.bot.send_message(
            update.effective_chat.id,
            "You must reply to a message to use this command."
        )
