import json
from aiogram import Router, F
from aiogram.filters import StateFilter, Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext

from src.data import Text, Markup
from src.states import PaymentsStates
from src.utils import BalanceOperation

rname = 'payments'
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

@router.callback_query(F.data == 'top_up')
async def new_top_up_handler(call: CallbackQuery, state: FSMContext):
    back_message = await call.message.edit_text(
        text=Text.get_amount, 
        reply_markup=Markup.configurator([Markup.back('profile')])
    )
    await state.set_state(PaymentsStates.get_amount)
    await state.set_data({
        "back_mess_id": back_message.message_id
    })

@router.message(Command("refund"))
async def refund_command(message: Message):
    args = message.text.split()

    data = load_users()
    if not is_admin(message.from_user.id, data):
        return await message.answer("⛔️ У тебя нет прав для этой команды.")

    if len(args) != 3:
        return await message.answer("⚠️ Использование: /refund <user_id> <telegram_payment_charge_id>")

    user_id = args[1]
    telegram_payment_charge_id = args[2]

    if not user_id:
        return await message.answer("❌ Транзакция не найдена.")

    try:
        result = await message.bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=telegram_payment_charge_id
        )

        if result:
            await message.answer("✅ Возврат успешно оформлен.")
        else:
            await message.answer("❌ Не удалось выполнить возврат.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при возврате: {e}")


@router.message(StateFilter(PaymentsStates.get_amount))
async def create_invoice(message: Message, state: FSMContext):
    data = await state.get_data()

    await message.bot.delete_message(
        chat_id=message.chat.id, 
        message_id=data['back_mess_id']
    )

    if not message.text.isnumeric():
        return await message.answer(
            text=Text.errors.not_integer,
            reply_markup=Markup.configurator([Markup.back('profile')])
        )
    
    await message.answer(
        text=Text.invoice_emoji,
        reply_markup=Markup.cancel_invoice
    )
    
    amount = int(message.text)
    invoice_id = await message.bot.database.create_invoice(amount)

    invoice_message = await message.answer_invoice(
        title="💎 Giftomatic — пополнение баланса",
        description="Пополнение баланса для автозакупки подарков",
        payload=str(invoice_id),
        provider_token="",
        currency="XTR",
        prices=[
            LabeledPrice(
                label="Пополнение баланса",
                amount=amount
            )
        ]
    )
    await message.bot.database.additional_message_id_invoice(
        invoice_id, invoice_message.message_id
    )
    await state.set_data({
        "invoice_id": invoice_id
    })
    await state.set_state(PaymentsStates.wait_payment)


@router.pre_checkout_query(StateFilter(PaymentsStates.wait_payment))
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    is_pending = await pre_checkout_query.bot.database.is_invoice_pending(
        int(pre_checkout_query.invoice_payload)
    )
    
    if is_pending:
        await pre_checkout_query.answer(ok=True)
    else:
        await pre_checkout_query.answer(
            ok=False,
            error_message=Text.errors.invoice_reject
        )


@router.message(F.successful_payment, StateFilter(PaymentsStates.wait_payment))
async def process_successful_payment(message: Message, state: FSMContext):
    invoice_id = int(message.successful_payment.invoice_payload)
    back_message_id = await message.bot.database.get_invoice_message_id(invoice_id, True)

    await message.bot.database.update_balance(
        message.from_user.id, 
        message.successful_payment.total_amount,
        operation=BalanceOperation.ADD
    )

    await message.bot.delete_message(
        chat_id=message.chat.id, 
        message_id=back_message_id
    )
    
    await message.answer(
        text=Text.success_invoice_emoji, 
        reply_markup=Markup.start
    )
    await message.answer(
        text=Text.successful_invoice,
        reply_markup=Markup.configurator([Markup.back('profile')])
    )
    
    await state.clear()


@router.callback_query(F.data == 'buy_vip')
async def vip_info_handler(call: CallbackQuery):
    await call.message.edit_text(
        text=Text.vip_text.format(call.bot.config.vip_price),
        reply_markup=Markup.configurator(
            [Markup.buy_vip],
            [Markup.back('profile')]
        )
    )


@router.callback_query(F.data == 'invoice_buy_vip')
async def vip_buy_handler(call: CallbackQuery):
    user_db = await call.bot.database.get_user(call.from_user.id)
    
    if user_db.vip:
        return await call.answer(
            text=Text.errors.already_buy, show_alert=True
        )

    if user_db.balance < call.bot.config.vip_price:
        return await call.answer(
            text=Text.errors.insufficient_funds,
            show_alert=True
        )
    
    await call.bot.database.update_balance(
        call.from_user.id, 
        call.bot.config.vip_price,
        operation=BalanceOperation.SUBTRACT
    )
    await call.bot.database.grant_vip(call.from_user.id, True)
    
    await call.message.edit_text(
        text=Text.success_buy_vip,
        reply_markup=Markup.configurator(
            [Markup.back('profile')]
        )
    )