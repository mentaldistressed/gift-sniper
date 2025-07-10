import json
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.data import Text, Markup
from src.config import Config
from src.utils import DefaultUtils, CustomCall, CustomMessage
from src.states import PaymentsStates
from src.data.database import Database

USERS_FILE = "users.json"

rname = 'info'
router = Router()

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        data = {"whitelist": [], "admins": []}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data


def save_users(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def is_admin(user_id: int, data=None) -> bool:
    data = data or load_users()
    return user_id in data.get("admins", [])

@router.message(Command("info"))
async def info_handler(message: Message):
    data = load_users()
    if not is_admin(message.from_user.id, data):
        return
    config: Config = message.bot.config
    user = await message.bot.database.get_user(
        message.from_user.id
    )

    await message.answer(
        text=Text.info.format(
            startup_date=message.bot.startup_date,
            user_count=await message.bot.database.get_user_count(),
            storage=await message.bot.database.get_total_balance(),
            all_buy=await message.bot.database.get_total_gifts(),
            interval=config.vip_poll_interval if user.vip else config.default_poll_interval
        ), reply_markup=Markup.settings(config.admin_url)
    )

@router.callback_query(F.data == 'settings')
async def settings_handler(call: CallbackQuery):
    user = await call.bot.database.get_user(
        call.from_user.id
    )
    await call.message.edit_text(
        text=Text.info_setting,
        reply_markup=Markup.setting_generator(user.buying_mode)
    )