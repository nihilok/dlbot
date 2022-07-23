import asyncio
import json
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

USER_FILE = 'dl_bot/users.json'


class UnauthorizedUserException(Exception):
    def __init__(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        loop = asyncio.get_running_loop()
        loop.create_task(context.bot.send_message(
            update.effective_chat.id,
            'You are not authorised to perform this action.'
        ))
        super().__init__()


def get_users():
    with open(USER_FILE, 'r') as f:
        try:
            return json.load(f)
        except FileNotFoundError as e:
            print(e)
            with open('dl_bot/users.json', 'w') as g:
                json.dump({"superuser": 0, "users": [], "chats": []}, g)
            return get_users()


async def check_auth(update: Update):
    users = get_users()
    if update.effective_chat.id in users["chats"]:
        return True
    if (user_id := update.effective_user.id) in users['users']:
        return True
    if user_id == users['superuser']:
        return True
    return False


def require_superuser(f):
    @wraps(f)
    async def wrapped_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_dict = get_users()
        superuser = user_dict["superuser"]
        if update.effective_user.id != superuser:
            raise UnauthorizedUserException(update, context)
        return await f(update, context)

    return wrapped_handler


async def add_user(user_id: int):
    users = get_users()
    user_set = set(users["users"])
    user_set.add(user_id)
    users["users"] = list(user_set)
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)


async def remove_user(user_id: int):
    users = get_users()
    if user_id not in users["users"]:
        return
    users["users"].remove(user_id)
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)


async def add_group(chat_id: int):
    users = get_users()
    chat_set = set(users["chats"])
    chat_set.add(chat_id)
    users["chats"] = list(chat_set)
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)


async def remove_group(chat_id: int):
    users = get_users()
    if chat_id not in users["chats"]:
        return
    users["chats"].remove(chat_id)
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)
