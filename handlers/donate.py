import asyncio
import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from datetime import datetime, timedelta
from typing import Any
from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from common import keyboard


# Инициализируем роутер уровня модуля
donate_router = Router()

# Фильтрация сообщений для обработки только в приватных чатах
donate_router.message.filter(F.chat.type == "private")

# Определение класс состояний для валюты
class Donate(StatesGroup):
    """Класс состояний для доната"""
    donate_input = State()
    donate_input_x = State()
    donate_send = State()

# Условие для возврата: возврат возможен только в течение 30 дней после доната
REFUND_PERIOD_DAYS = 30


@donate_router.message(Command("donate"))
async def cmd_donate(message: Message, state: FSMContext):
    # await message.answer(text=_('Поддержать автора донатом'), reply_markup=keyboard.del_kb)
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="10 ⭐️",callback_data="donate_10"))
    builder.row(InlineKeyboardButton(text="50 ⭐️",callback_data="donate_50"))
    builder.row(InlineKeyboardButton(text="100 ⭐️", callback_data="donate_100"))
    builder.row(InlineKeyboardButton(text=_("другое"),callback_data="donate_x"))
    builder.row(InlineKeyboardButton(text=_("Назад на главную ↩️"), callback_data='donate_back'))
    await message.answer(text=_("Поддержать автора донатом"), reply_markup=builder.adjust(2,2,1).as_markup())
    await state.set_state(Donate.donate_input)


@donate_router.callback_query(Donate.donate_input, F.data.startswith("donate_"))
async def cmd_donate_input(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_")[1]

    if data == 'back':
        await state.set_state(None)
        await callback.message.edit_text(text=_("Поддержать автора донатом"), reply_markup=None)
        await callback.answer(_('Назад на главную'))
        await asyncio.sleep(1)
        await callback.message.answer(_('Главная панель'), reply_markup=keyboard.start_keyboard())


    elif data == 'x':
        # await callback.message.edit_text(text="Поддержать автора донатом", reply_markup=None)
        await callback.message.delete()
        await callback.message.answer(text=_('Введите произвольную сумму доната, от 1 до 2500 ⭐️'), reply_markup=keyboard.del_kb)
        await state.set_state(Donate.donate_input_x)

    else:
        amount = int(data)
        await state.update_data(donate_amount=amount)
        await callback.message.delete()

        # Формируем клавиатуру с кнопками для оплаты и отмены операции
        kb = InlineKeyboardBuilder()
        kb.button(text=_("{amount} XTR").format(amount=amount), pay=True)  # pay=True важный параметр, указывающий что кнопка предназначена для оплаты
        kb.button(text=_("Отменить"), callback_data="donate_cancel")
        kb.adjust(1)

        # Формируем инвойс для оплаты
        prices = [LabeledPrice(label="XTR", amount=amount)]
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        await callback.message.answer_invoice(title=_("Поддержать автора донатом"),
                                                description=_("На сумму"),
                                                prices=prices,
                                                provider_token="",
                                                payload=timestamp,  # Добавляем временную метку в payload
                                                currency="XTR",
                                                reply_markup=kb.as_markup()
                                            )
        await state.set_state(Donate.donate_send)


@donate_router.message(Donate.donate_input_x)
async def cmd_donate_input_x(message: Message,  state: FSMContext):
    text = message.text
    if text.isdigit() and 1 <= int(text) <= 2500: # type: ignore
        amount = int(text) # type: ignore
        await state.update_data(donate_amount=amount)
        await message.delete()

        # Формируем клавиатуру с кнопками для оплаты и отмены операции
        kb = InlineKeyboardBuilder()
        kb.button(text=_("{amount} XTR").format(amount=amount), pay=True)  # pay=True важный параметр, указывающий что кнопка предназначена для оплаты
        kb.button(text=_("Отменить"), callback_data="donate_cancel")
        kb.adjust(1)

        # Формируем инвойс для оплаты
        prices = [LabeledPrice(label="XTR", amount=amount)]
        timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        await message.answer_invoice(title=_("Поддержать автора донатом"),
                                    description=_("На сумму"),
                                    prices=prices,
                                    provider_token="",
                                    payload=timestamp,  # Добавляем временную метку в payload
                                    currency="XTR",
                                    reply_markup=kb.as_markup()
                                    )
        await state.set_state(Donate.donate_send)

    else:
        await message.answer(text=_('Telegram может принять донат только в диапазоне от 1 до 2500 ⭐️.\n\nВведите любое целое число из данного диапазона.'),
                             reply_markup=keyboard.del_kb)


# Обработка отмены доната, выводим сообщение об отмене и удаляем сообщение
@donate_router.callback_query(Donate.donate_send, F.data == "donate_cancel")
async def on_donate_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer(_("😢 Донат отменен."))
    await callback.message.delete()
    await state.set_state(None)
    await state.update_data(donate_amount=None)
    await callback.message.answer(_('Главная панель'), reply_markup=keyboard.start_keyboard())

# Обработка команды возврата доната (без ограничения по времени)
@donate_router.message(Command('refundd'))
async def command_refund_handler(message: Message, bot: Bot, command: CommandObject) -> None:
    transaction_id = command.args if command.args else ''
    user_id = message.from_user.id
    try:
        await bot.refund_star_payment(user_id=user_id, telegram_payment_charge_id=transaction_id)
    except Exception as e:
        logger.error("Ошибка: %s", str(e))

# Обработка команды возврата доната (с ограничением по времени)
@donate_router.message(Command("refund"))
async def cmd_refund(message: Message, bot: Bot, command: CommandObject, state: FSMContext):
    # ID транзакции для возврата средств
    t_id = command.args
    # Проверяем, указан ли ID транзакции
    if t_id is None:
        await message.answer(_("Пожалуйста, укажите идентификатор транзакции в формате <code>/refund [id]</code>, "
                                "где <code>[id]</code> это идентификатор транзакции, который вы получили после доната.\n\n"
                                "/terms - условия использования\n"
                                "/id_trans - ID транзакции"))
        return
    # Проверяем, не истек ли срок возврата
    try:
        # Извлекаем временную метку из donate_info
        data = await state.get_data()
        donate_info: dict = data.get('donate_info', {})
        timestamp: Any = donate_info.get(t_id, '')  # получаем временную метку в формате строки, по id транзакции
        # Парсим строку в объект datetime
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d-%H-%M-%S")
        # Получаем текущую дату и время
        current_time = datetime.now()
        # Вычисляем разницу во времени
        time_difference = current_time - timestamp
        if time_difference > timedelta(days=REFUND_PERIOD_DAYS):
            await message.answer(_("Срок для возврата средств истек. Возврат возможен только в течение 30 дней после доната."))
            return
    # Если не удалось распарсить временную метку, выводим сообщение об ошибке
    except (ValueError, IndexError) as e:
        logger.error("Ошибка: %s", str(e))
        await message.answer(_("Неверный формат идентификатора транзакции."))
        return
    # Пытаемся сделать возврат средств
    try:
        await bot.refund_star_payment(user_id=message.from_user.id, telegram_payment_charge_id=t_id)
        await message.answer(_("Рефанд произведен успешно. Потраченные звёзды уже вернулись на ваш счёт в Telegram."))
    except TelegramBadRequest as e:
        logger.error("Ошибка: %s", str(e))
        err_text = _("Транзакция с указанным идентификатором не найдена. Пожалуйста, проверьте введенные данные и повторите ещё раз.")
        if "CHARGE_ALREADY_REFUNDED" in e.message:
            err_text = _("Рефанд по этой транзакции уже был ранее произведен.")
        await message.answer(err_text)
        return


# Проверка перед оплатой, бот должен ответить в течение 10 секунд
@donate_router.pre_checkout_query(Donate.donate_send)
async def pre_checkout_query(query: PreCheckoutQuery):
    # Мы всегда отвечаем положительно, так как это просто донат
    await query.answer(ok=True)

    # Если по какой-то причине нужно отказать в проведении платежа, можно использовать:
    # Добавляем условие для проверки ..
    # await query.answer(ok=False, error_message="Причина отказа в проведении платежа")


# Обработка успешного платежа
@donate_router.message(Donate.donate_send, F.successful_payment)
async def on_successfull_payment(message: Message, state: FSMContext, workflow_data: dict):
    # Получаем объект message.successful_payment
    t_id = message.successful_payment.telegram_payment_charge_id  # ID транзакции
    invoice_payload = message.successful_payment.invoice_payload  # payload который мы установили ранее, там временная метка
    user_id = message.from_user.id

    data = await state.get_data()
    donate_info = data.get('donate_info', {})
    donate_info[t_id] = invoice_payload
    print('donate_info: ', donate_info)
    await state.update_data(donate_info=donate_info)

    await message.answer(
        text=_("<b>Спасибо!</b>\n"
               "Ваш донат успешно принят.\n\n"
                "ID транзакции:\n<code>{t_id}</code>").format(t_id=t_id),
        message_effect_id="5104841245755180586"
    )
        # другие реакции (если надо)
        # 🔥 огонь - 5104841245755180586
        # 👍 лайк - 5107584321108051014
        # 👎 дизлайк - 5104858069142078462
        # ❤️ сердечко - 5159385139981059251
        # 🎉 праздник - 5046509860389126442
        # 💩 какаха - 5046589136895476101

    await state.set_state(None)
    await state.update_data(donate_amount=None)

    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/income",
                    command_name="/donate")

# Отправляем сообщение с инструкциями по поддержке покупок
@donate_router.message(Command("id_trans"))
async def cmd_id_trans(message: Message, state: FSMContext):
    data = await state.get_data()
    donate_info = data.get('donate_info', {})
    t_id = max(donate_info, key=donate_info.get) if donate_info else _('ID транзакции не найден')
    await message.answer(
        text=_('Чтобы оформить возврат, вам понадобится ID транзакции.\n\nID последней вашей транзакции:\n<code>{t_id}</code>').format(t_id=t_id))

# Отправляем условия использования бота (Terms of Service)
@donate_router.message(Command("terms"))
async def cmd_terms(message: Message):
    await message.answer(_("<b>Условия использования</b>\n\n"
                            "1. Донаты являются добровольными и могут быть возвращены в течение 30 дней после совершения платежа.\n\n"
                            "2. Для возврата средств необходимо предоставить идентификатор транзакции. Получить ID транзакции /id_trans\n\n"
                            "3. После истечения 30 дней возврат средств невозможен.\n\n"
                            "4. Использование бота подразумевает согласие с данными условиями.\n\n")
                            )
