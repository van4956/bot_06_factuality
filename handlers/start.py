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
from database.orm_answers import orm_get_answer
from common import keyboard


# Инициализируем роутер уровня модуля
start_router = Router()

# Команда /start
@start_router.message(CommandStart())
async def start_cmd(message: Message, session: AsyncSession, bot: Bot, workflow_data: dict):
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
        if user_id not in list_users:
            await bot.send_message(chat_id=chat_id, text=_("✅ @{user_name} - подписался на бота").format(user_name=user_name,
                                                                                                                        user_id=user_id))
            await message.answer(text=_('{user_name}, добро пожаловать в Factuality Test!\n\n'
                                        'Текущий язык: Русский 🇷🇺 \n\n'
                                        'Желаете сменить язык?\n'
                                        'Используйте /language').format(user_name=user_name))
            await message.answer(text=_('Этот бот основан на книге Ганса Рослинга «Фактологичность». '
                                        'Пройдите тест из 13 вопросов, чтобы узнать, насколько точно вы воспринимаете мировые тенденции.\n\n'
                                        'Готовы пройти тест?'),
                                reply_markup=keyboard.inline_start_test())
            await orm_add_user(session, data)

            await analytics(user_id=user_id,
                            category_name="/start",
                            command_name="/start")

        elif user_id in list_users:
            await message.answer(text=_('Текущий язык: Русский 🇷🇺 \n\n'
                                        'Желаете сменить язык?\n'
                                        'Используйте /language'))

            current_answer = await orm_get_answer(session, user_id)
            if current_answer == 1:
                await message.answer(text=_('Factuality Test\n\n'
                                            'Готовы пройти тест?'),
                                     reply_markup=keyboard.inline_start_test())
            elif current_answer == 0:
                await message.answer(text=_('Factuality Test\n\n'
                                            'Вы уже прошли тест!'))
            else:
                await message.answer(text=_('Factuality Test\n\n'
                                            'Желаете продолжить тест?'),
                                     reply_markup=keyboard.inline_continue_test())

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
