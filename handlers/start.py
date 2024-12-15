import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from aiogram import F, Router, Bot
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message, FSInputFile
from aiogram.filters import ChatMemberUpdatedFilter, KICKED, MEMBER
from aiogram.fsm.context import FSMContext
from aiogram.types import ChatMemberUpdated
from aiogram.utils.i18n import gettext as _

from database.orm_users import orm_add_user, orm_get_ids, orm_get_users, orm_update_status
from database.orm_answers import orm_get_answer, orm_get_current_question, orm_update_current_question, orm_create_answer, orm_get_result
from common import keyboard


# Инициализируем роутер уровня модуля
start_router = Router()

# Команда /start
@start_router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession, bot: Bot, workflow_data: dict, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.username if message.from_user.username else 'None'
    full_name = message.from_user.full_name if message.from_user.full_name else 'None'
    locale = message.from_user.language_code if message.from_user.language_code else 'ru'
    data = {'user_id':user_id,
                            'user_name':user_name,
                            'full_name':full_name,
                            'locale':locale,
                            'status':'member',
                            'flag':1}

    try:
        analytics = workflow_data['analytics']
        list_users = [user_id for user_id in await orm_get_ids(session)]
        chat_id = bot.home_group[0]

        # если юзер не в базе, то есть впервые написал боту
        if user_id not in list_users:
            await bot.send_message(chat_id=chat_id, text=f"✅ @{user_name} - подписался на бота")
            new_message = await message.answer(text=_('{user_name}, добро пожаловать в Factuality Test!\n\n'
                                        'Этот бот создан на основе книги Ханса Рослинга «Фактологичность». '
                                        'Пройдите тест из 13 вопросов, чтобы проверить, насколько верно вы понимаете мировые тенденции.\n\n'
                                        'Готовы пройти тест?').format(user_name=user_name),
                                reply_markup=keyboard.inline_start_test())
            # Добавляем записи нового юзера в таблицы
            await orm_add_user(session, data)
            await orm_create_answer(session, user_id)

            # Сохраняем новый message_id
            await state.update_data(last_message_id=new_message.message_id)

            await analytics(user_id=user_id,
                            category_name="/start",
                            command_name="/start")

        # если юзер уже в базе
        elif user_id in list_users:

            # Удаляем команду /start пользователя
            await message.delete()

            # Получаем сохраненный message_id и current_question из FSM
            data = await state.get_data()
            last_message_id = data.get('last_message_id')
            orm_current_question = await orm_get_current_question(session, user_id)
            current_question = data.get('current_question', orm_current_question)

            # Если есть предыдущее сообщение, удаляем его
            if last_message_id:
                try:
                    await message.bot.delete_message(chat_id=message.chat.id,
                                                    message_id=last_message_id)
                except Exception as e:
                    logger.error("Ошибка при удалении сообщения: %s", e)

            # Отправляем новое сообщение с учетом текущего вопроса
            if current_question == 1:
                new_message = await message.answer(text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
                                            'Готовы пройти тест?'),
                                     reply_markup=keyboard.inline_start_test())
            elif current_question > 13:
                data = await state.get_data()
                orm_correct_count = await orm_get_result(session, user_id)
                correct_count = data.get('result', orm_correct_count)
                new_message = await message.answer(text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
                                            'Вы прошли тест!\n\n'
                                            'Ваш результат: {correct_count}/13\n').format(correct_count=correct_count),
                                     reply_markup=keyboard.get_callback_btns(btns={'Правильные ответы':'correct_answers',
                                                                                 'О книге':'about_book',
                                                                                 'О тесте':'about_test'},
                                                                            sizes=(1,1,1)))
            else:
                new_message = await message.answer(text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
                                            'Вы остановились на {current_question} вопросе. \n'
                                            'Желаете продолжить тест?').format(current_question=current_question),
                                     reply_markup=keyboard.inline_continue_test())

            # Сохраняем новый message_id
            await state.update_data(last_message_id=new_message.message_id)

            await analytics(user_id=user_id,
                            category_name="/start",
                            command_name="/restart")

    except Exception as e:
        logger.error("Ошибка при отправке сообщения: %s", str(e))



# Этот хэндлер будет срабатывать на блокировку бота пользователем
@start_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def process_user_blocked_bot(event: ChatMemberUpdated, session: AsyncSession, bot: Bot, workflow_data: dict):
    user_id = event.from_user.id
    chat_id = bot.home_group[0]
    user_name = event.from_user.username if event.from_user.username else event.from_user.full_name
    await orm_update_status(session, user_id, 'kicked')
    await bot.send_message(chat_id = chat_id, text = f"⛔️ @{user_name} - заблокировал бота")

    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/start",
                    command_name="/blocked")

# Этот хэндлер будет срабатывать на разблокировку бота пользователем
@start_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def process_user_unblocked_bot(event: ChatMemberUpdated, session: AsyncSession, bot: Bot, workflow_data: dict):
    user_id = event.from_user.id

    if user_id in await orm_get_ids(session):
        chat_id = bot.home_group[0]
        full_name = event.from_user.full_name if event.from_user.full_name else "NaN"
        user_name = event.from_user.username if event.from_user.username else full_name
        await orm_update_status(session, user_id, 'member')
        await bot.send_message(chat_id = user_id, text = _('{full_name}, Добро пожаловать обратно!').format(full_name=full_name))
        await bot.send_message(chat_id = chat_id, text = f"♻️ @{user_name} - разблокировал бота")

        analytics = workflow_data['analytics']
        await analytics(user_id=user_id,
                        category_name="/start",
                        command_name="/unblocked")
