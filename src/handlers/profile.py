from aiogram import Router, F
from aiogram.types import Message

from src.data import Text, Markup
from src.utils import DefaultUtils
from src.data.database import User


rname = 'based'
router = Router()


@router.callback_query(F.data == 'profile')
async def profile1_handler(message: Message):
    user_info: User = await message.bot.database.get_user(
        message.from_user.id
    )
    await call.message.edit_text(
        text=Text.profile.format(
            user=DefaultUtils.remove_html_tags(message.from_user.full_name),
            id=message.from_user.id,
            balance=int(user_info.balance),
            status_vip=Text.utils.bool_to_emoji(user_info.vip),
            default_interval=message.bot.config.default_poll_interval,
            vip_interval=message.bot.config.vip_poll_interval
        ),
        reply_markup=Markup.profile
    )

@router.message(F.text == '👤 Профиль')
async def profile_handler(message: Message):
    user_info: User = await message.bot.database.get_user(
        message.from_user.id
    )
    await message.answer(
        text=Text.profile.format(
            user=DefaultUtils.remove_html_tags(message.from_user.full_name),
            id=message.from_user.id,
            balance=int(user_info.balance),
            status_vip=Text.utils.bool_to_emoji(user_info.vip),
            default_interval=message.bot.config.default_poll_interval,
            vip_interval=message.bot.config.vip_poll_interval
        ),
        reply_markup=Markup.profile
    )