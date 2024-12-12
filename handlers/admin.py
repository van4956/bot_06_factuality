import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, CommandObject, StateFilter, or_f
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.context import FSMContext

from filters.is_admin import IsAdminGroupFilter, IsAdminListFilter
from filters.chat_type import ChatTypeFilter
from common import keyboard
from database.orm_users import orm_get_users


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdminListFilter(is_admin=True))


# команда /admin
@admin_router.message(Command("admin"))
async def cmd_admin(message: Message, bot: Bot):
    if message.from_user.id in bot.admin_list:
        await message.answer(text=_('Админка:\n\n'
                                    '/start - перезапустить бота\n'
                                    '/data - состояние FSMContext\n'
                                    '/get_id - id диалога\n'
                                    '/ping - количество апдейтов\n'
                                    '/users - пользователи\n'
                                    '/admins - админы\n'),
                            reply_markup=keyboard.del_kb
                            )


# команда /users, показывает полную информацию всех зарегистрированных пользователей
@admin_router.message(or_f(Command("users"), F.text == "Информация о пользователях"))
async def get_users_info(message: Message, session: AsyncSession):
    all_info = ['Информация зарегистрированных пользователей:\n']
    cnt_users = 0
    len_text = len(all_info)

    for user in await orm_get_users(session):
        user_status = 'm' if user.status == 'member' else 'k'
        info = f"<code>{user.user_id: <11}</code> | <code>{user_status}</code> | {user.flag} | {user.locale} | <code>{user.user_name[:11]}</code>"
        cnt_users += 1

        # если длина текста больше 4000 символов, то пропускаем добавление новой строки в список
        if len_text + len(info) > 4000:
            continue
        all_info.append(info)

    text = "\n".join(all_info) + f"\n\nВсего {cnt_users} пользователей"

    await message.answer(text)


# Here is some example !ping command ...
@admin_router.message(Command(commands=["ping"]),)
async def cmd_ping_bot(message: Message, counter):
    await message.reply(f"ping-{counter}")


# Этот хендлер показывает ID чата в котором запущена команда
@admin_router.message(Command("get_id"))
async def get_chat_id_cmd(message: Message):
    await message.answer(f"ID: <code>{message.chat.id}</code>")

# команда /admins, показывает состав всех админов
@admin_router.message(Command("admins"))
async def get_admins_info(message: Message, bot: Bot):
    list_admins = '\n'.join([f"<code>{str(id)}</code>" for id in bot.admin_list])
    await message.answer(f"Админы:\n\n{list_admins}")

# секретный хендлер, покажет содержимое data пользователя
@admin_router.message(F.text == "..")
async def data_cmd(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(str(data))
