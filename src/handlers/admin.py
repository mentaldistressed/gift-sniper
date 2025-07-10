from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from src.data import Text, Markup
from src.utils import DefaultUtils, BalanceOperation

rname = 'admin'
router = Router()


def is_owner_filter(message: Message):
    return message.from_user.id == message.bot.config.owner


@router.message(Command('givevip'), is_owner_filter)
async def give_vip_handler(message: Message):
    try:
        user_id = int(message.text.split()[1])
        user = await message.bot.database.get_user(user_id)
        
        if not user:
            return await message.answer("❌ Пользователь не найден")
            
        await message.bot.database.grant_vip(user_id, True)
        await message.answer(f"✅ VIP-статус выдан пользователю {user_id}")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /give_vip <user_id>")


@router.message(Command('removevip'), is_owner_filter)
async def remove_vip_handler(message: Message):
    try:
        user_id = int(message.text.split()[1])
        user = await message.bot.database.get_user(user_id)
        
        if not user:
            return await message.answer("❌ Пользователь не найден")
            
        await message.bot.database.grant_vip(user_id, False)
        await message.answer(f"✅ VIP-статус удален у пользователя {user_id}")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /remove_vip <user_id>")


@router.message(Command('givestars'), is_owner_filter)
async def give_stars_handler(message: Message):
    try:
        args = message.text.split()
        user_id = int(args[1])
        amount = int(args[2])
        
        user = await message.bot.database.get_user(user_id)
        if not user:
            return await message.answer("❌ Пользователь не найден")
            
        await message.bot.database.update_balance(user_id, amount, BalanceOperation.ADD)
        await message.answer(f"✅ {amount} звезд выдано пользователю {user_id}")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /give_stars <user_id> <amount>")


@router.message(Command('removestars'), is_owner_filter)
async def remove_stars_handler(message: Message):
    try:
        args = message.text.split()
        user_id = int(args[1])
        amount = int(args[2])
        
        user = await message.bot.database.get_user(user_id)
        if not user:
            return await message.answer("❌ Пользователь не найден")
            
        if user.balance < amount:
            return await message.answer("❌ У пользователя недостаточно звезд")
            
        await message.bot.database.update_balance(user_id, amount, BalanceOperation.SUBTRACT)
        await message.answer(f"✅ {amount} звезд удалено у пользователя {user_id}")
    except (IndexError, ValueError):
        await message.answer("❌ Использование: /remove_stars <user_id> <amount>")


