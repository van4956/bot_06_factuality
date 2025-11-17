import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from aiogram import Router, F, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.i18n import gettext as _

from database.orm_users import orm_update_locale
from database.orm_answers import orm_get_current_question
from common import keyboard

# Инициализируем роутер уровня модуля
other_router = Router()


# Клавиатура выбора языка
def keyboard_language():
    button_1 = InlineKeyboardButton(text=_('🇬🇧 Английский'), callback_data='locale_en')
    button_2 = InlineKeyboardButton(text=_('🇷🇺 Русский'), callback_data='locale_ru')
    # button_3 = InlineKeyboardButton(text=_('🇩🇪 Немецкий'), callback_data='locale_de')
    # button_4 = InlineKeyboardButton(text=_('🇫🇷 Французский'), callback_data='locale_fr')
    button_6 = InlineKeyboardButton(text=_('↩️ Назад'), callback_data='back_to_main')

    return InlineKeyboardMarkup(inline_keyboard=[[button_1, button_2],
                                                #  [button_3, button_4],
                                                 [button_6]])


# Это хендлер будет срабатывать на команду /language
@other_router.message(Command('language'))
async def language_cmd(message: Message, state: FSMContext, workflow_data: dict):
    # Получаем сохраненный message_id из FSM
    data = await state.get_data()
    last_message_id = data.get('last_message_id')

    # Удаляем команду пользователя
    await message.delete()

    # Если есть предыдущее сообщение, удаляем его
    if last_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=last_message_id
            )
        except Exception as e:
            logger.error("Ошибка при удалении сообщения: %s", e)

    # Отправляем новое сообщение
    new_message = await message.answer(
        text=_('Настройки языка\n'
               'Текущий язык: Русский 🇷🇺 \n\n'
               'Выберите язык, на котором будет работать бот'),
        reply_markup=keyboard_language()
    )

    # Сохраняем новый message_id
    await state.update_data(last_message_id=new_message.message_id)

    user_id = message.from_user.id
    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/options",
                    command_name="/language")

# Хендлер на нажатие кнопки выбора языка
@other_router.callback_query(F.data.startswith("locale_"))
async def update_locale_cmd(callback: CallbackQuery, session: AsyncSession, state: FSMContext, workflow_data: dict):
    user_id = callback.from_user.id
    if callback.data == 'locale_en':
        await orm_update_locale(session, user_id, 'en')  # Обновляем локаль в бд
        await state.update_data(locale='en')  # Обновляем локаль в контексте
        # удаляем прошлое сообщение, и отправляем новое
        await callback.message.delete()
        new_message = await callback.message.answer(text=("Settings language \n"
                                            "Current language: English 🇬🇧 \n\n"
                                            "Select the language in which the bot will work"),
                                      reply_markup=keyboard.get_callback_btns(btns={'🇬🇧 English':'locale_en',
                                                                                    '🇷🇺 Russian':'locale_ru',
                                                                                    '↩️ Back': 'back_to_main'},
                                                                                    sizes=(2,1)))
        await callback.answer("Selected: English 🇺🇸 ")  # Отправляем всплывашку

    # elif callback.data == 'locale_ru':
    else:
        await orm_update_locale(session, user_id, 'ru')  # Обновляем локаль в бд
        await state.update_data(locale='ru')  # Обновляем локаль в контексте
        await callback.message.delete()
        new_message = await callback.message.answer(text=('Настройки языка \n'
                                            'Текущий язык: Русский 🇷🇺\n\n'
                                            'Выберите язык, на котором будет работать бот'),
                                      reply_markup=keyboard.get_callback_btns(btns={'🇬🇧 Английский':'locale_en',
                                                                                    '🇷🇺 Русский':'locale_ru',
                                                                                    '↩️ Назад': 'back_to_main'},
                                                                                    sizes=(2,1)))
        await callback.answer("Выбран: Русский язык 🇷🇺 ")  # Отправляем всплывашку


    # Сохраняем message_id текущего сообщения
    await state.update_data(last_message_id=new_message.message_id)

    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/options",
                    command_name="/language")


# хендлер на команду /information
@other_router.message(Command('information'))
async def information_cmd(message: Message, session: AsyncSession, workflow_data: dict, state: FSMContext):
    # Получаем сохраненный message_id из FSM
    data = await state.get_data()
    last_message_id = data.get('last_message_id')
    current_question = data.get('current_question', await orm_get_current_question(session, message.from_user.id))

    if current_question <= 13:
        reply_markup = keyboard.get_callback_btns(btns={_('↩️ Назад'): 'back_to_main'}, sizes=(1,1))
    else:
        reply_markup = keyboard.get_callback_btns(btns={_('Поддержать проект'):'donate',
                                                                                        _('↩️ Назад'): 'back_to_main'},
                                                                                    sizes=(1,1))

    # Удаляем команду пользователя
    await message.delete()

    # Если есть предыдущее сообщение, удаляем его
    if last_message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_message_id)
        except Exception as e:
            logger.error("Ошибка при удалении сообщения: %s", e)

    # Отправляем новое сообщение
    new_message = await message.answer(
        text=_('ℹ️ О боте Factuality Test\n\n'
            'Интерактивный тест из 13 вопросов о глобальных трендах. '
            'Проверьте, насколько точно вы представляете реальное состояние мира.\n\n'
            'Как работает бот:\n'
            '• Вопросы появляются последовательно через inline-кнопки\n'
            '• Сообщения обновляются, а не множатся в чате\n'
            '• После прохождения теста доступны объяснения ответов\n\n'
            'Важное уточнение:\n'
            'Книга и основанный на ней тест написаны в 2015 году. Сейчас 2025, за 10 лет некоторые цифры изменились '
            '(например, население Земли выросло с 7 до 8 млрд). '
            'Однако суть осталась той же - тест про когнитивные искажения и инстинкты, '
            'а не про точные цифры. Тренды сохранились.\n\n'
            'Совет:\n'
            'Проходите тест интуитивно, не гуглите ответы - так вы увидите свои реальные представления о мире.'),
        reply_markup=reply_markup)

    # Сохраняем message_id текущего сообщения
    await state.update_data(last_message_id=new_message.message_id)

    user_id = message.from_user.id
    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/info",
                    command_name="/information")


# хендлер на команду /terms
# @other_router.message(Command('terms'))
# async def terms_cmd(message: Message, workflow_data: dict, state: FSMContext):
#     # Получаем сохраненный message_id из FSM
#     data = await state.get_data()
#     last_message_id = data.get('last_message_id')

#     # Удаляем команду пользователя
#     await message.delete()

#     # Если есть предыдущее сообщение, удаляем его
#     if last_message_id:
#         try:
#             await message.bot.delete_message(
#                 chat_id=message.chat.id,
#                 message_id=last_message_id
#             )
#         except Exception as e:
#             logger.error("Ошибка при удалении сообщения: %s", e)

#     # Отправляем новое сообщение
#     new_message = await message.answer(text=_('📋 Условия использования Factuality Test\n\n'
#                                 'Используя этого бота, вы соглашаетесь со следующими условиями:\n\n'
#                                 '📊 Сбор данных:\n'
#                                 '• Мы сохраняем ваши ответы на вопросы теста\n'
#                                 '• Собираем базовую информацию профиля (имя пользователя, язык)\n'
#                                 '• Анализируем агрегированную статистику прохождения теста\n\n'
#                                 '🔒 Конфиденциальность:\n'
#                                 '• Все данные анонимизированы\n'
#                                 '• Мы не передаем персональные данные третьим лицам\n'
#                                 '• Используем информацию только для улучшения работы бота\n\n'
#                                 '❌ Отказ от использования:\n'
#                                 '• Чтобы остановить бота, заблокируйте его стандартными средствами Telegram\n'
#                                 '• При этом ваши данные будут удалены из статистики ответов\n\n'),
#                                 reply_markup=keyboard.get_callback_btns(btns={_('↩️ Назад'): 'back_to_main'},
#                                                 sizes=(1,1)))

    # # Сохраняем message_id текущего сообщения
    # await state.update_data(last_message_id=new_message.message_id)

    # user_id = message.from_user.id
    # analytics = workflow_data['analytics']
    # await analytics(user_id=user_id,
    #                 category_name="/info",
    #                 command_name="/terms")

# хендлер очистки фсм
@other_router.message(F.text == 'fsm')
async def fsm_cmd(message: Message, state: FSMContext):
    await message.delete()
    await state.clear()
    logger.info("FSM cleared")

# хендлер на получение сообщения от пользователя, и удаление его
@other_router.message()
async def echo(message: Message):
    await message.delete()
