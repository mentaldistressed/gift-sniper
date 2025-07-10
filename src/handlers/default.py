import json
from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

from src.data import Text, Markup
from src.utils import DefaultUtils, CustomCall
from src.states import PaymentsStates

from src.handlers.profile import profile_handler
from src.handlers.info import info_handler

rname = 'based'
router = Router()

USERS_FILE = "users.json"

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


def is_whitelisted(user_id: int, data=None) -> bool:
    data = data or load_users()
    return user_id in data.get("whitelist", [])


async def check_access(message: Message) -> bool:
    data = load_users()
    if is_admin(message.from_user.id, data) or is_whitelisted(message.from_user.id, data):
        return True
    await message.answer(
        f"❌ У Вас нет доступа к приватному боту\n\n"
        f"На данный момент доступ имеет {len(data.get('whitelist', []))} человек",
        reply_markup=ReplyKeyboardRemove()
    )
    return False


async def check_access_callback(call: CallbackQuery) -> bool:
    data = load_users()
    if is_admin(call.from_user.id, data) or is_whitelisted(call.from_user.id, data):
        return True
    await call.answer(
        f"❌ У Вас нет доступа к приватному боту\n\n"
        f"На данный момент доступ имеет {len(data.get('whitelist', []))} человек",
        show_alert=True
    )
    return False

@router.callback_query(F.data == 'faq')
async def new_top_up_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        text=Text.faq, 
        reply_markup=Markup.faq
    )

@router.message(CommandStart())
async def start_handler(message: Message):
    if not await check_access(message):
        return
    await message.bot.database.create_user(message.from_user.id)
    await message.answer(
        text=Text.start.format(user=DefaultUtils.remove_html_tags(message.from_user.full_name)),
        reply_markup=Markup.start
    )


@router.callback_query(F.data.split('|')[0] == 'back')
async def back_handler(call: CallbackQuery, state: FSMContext):
    if not await check_access_callback(call):
        return
    await state.clear()
    back_argument = call.data.split('|')[1]
    if back_argument == 'profile':
        await profile_handler(CustomCall(call))
    elif back_argument == 'info':
        await info_handler(CustomCall(call))


@router.message(F.text == 'Отмена', StateFilter(PaymentsStates.wait_payment))
async def cancel_handler_invoice(message: Message, state: FSMContext):
    if not await check_access(message):
        return
    invoice_id = (await state.get_data())["invoice_id"]
    invoice_message_id = await message.bot.database.get_invoice_message_id(invoice_id, False)

    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=invoice_message_id
    )
    await state.clear()
    await start_handler(message)


@router.callback_query(F.data == 'dev')
async def in_development_handler(call: CallbackQuery):
    if not await check_access_callback(call):
        return
    await call.answer(
        text=Text.in_development, show_alert=True
    )

@router.message(Command("add"))
async def add_user(message: Message):
    data = load_users()
    if not is_admin(message.from_user.id, data):
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.answer("⚠️ Использование: /add [user_id]")
    user_id = int(args[1])
    if user_id in data["whitelist"]:
        return await message.answer("❌ Пользователь уже в вайтлисте.")
    data["whitelist"].append(user_id)
    save_users(data)
    await message.answer(f"✅ Пользователь {user_id} добавлен в вайтлист.")


@router.message(Command("remove"))
async def remove_user(message: Message):
    data = load_users()
    if not is_admin(message.from_user.id, data):
        return
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        return await message.answer("⚠️ Использование: /remove [user_id]")
    user_id = int(args[1])
    if user_id not in data["whitelist"]:
        return await message.answer("❌ Пользователя нет в вайтлисте.")
    data["whitelist"].remove(user_id)
    save_users(data)
    await message.answer(f"✅ Пользователь {user_id} удалён из вайтлиста.")
