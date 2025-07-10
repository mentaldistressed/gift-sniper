from typing import Tuple, List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, \
                            ReplyKeyboardMarkup, KeyboardButton

class Markup:
    start = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='👤 Профиль')],
        [KeyboardButton(text='ℹ️ Информация')],
    ], resize_keyboard=True)

    # profile = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text='Пополнить баланс', callback_data='top_up')],
    #     [InlineKeyboardButton(text='🚀 Приобрести VIP', callback_data='buy_vip')]
    # ])

    profile = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Пополнить баланс', callback_data='top_up')]
        # [InlineKeyboardButton(text='🚀 Приобрести VIP', callback_data='buy_vip')]
    ])

    cancel_invoice = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Отмена')]
    ], resize_keyboard=True)

    buy_vip = InlineKeyboardButton(
        text='Приобрести навсегда', callback_data='invoice_buy_vip'
    )

    @staticmethod
    def setting_generator(mode: int) -> InlineKeyboardMarkup:
        is_active = lambda _mode: '✅' if mode == _mode else ''
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f'{is_active(0)} На весь баланс', callback_data='dev')],
                [InlineKeyboardButton(text=f'{is_active(1)} Процент от баланса', callback_data='dev')],
                [InlineKeyboardButton(text=f'{is_active(2)} Лимит звезд', callback_data='dev')],
                [Markup.back('info')]
            ]
        )
    
    @staticmethod
    def settings(admin_url: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Настройки', callback_data='settings')],
        [InlineKeyboardButton(text='🖥 Администрация', url=admin_url)]
    ])

    @staticmethod
    def back(back_type: str) -> InlineKeyboardButton:
        return InlineKeyboardButton(text='⬅️ Назад', callback_data=f'back|{back_type}')

    @staticmethod
    def configurator(*buttons: Tuple[List[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=list(buttons))