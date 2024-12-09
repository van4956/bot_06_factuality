import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from filters.is_owner import IsOwnerFilter
from filters.chat_type import ChatTypeFilter
from database.orm_users import orm_get_users, orm_update_status


owner_router = Router()
owner_router.message.filter(ChatTypeFilter(["group", "supergroup"]), IsOwnerFilter(is_owner=True))


"""функции доступные только владельцу бота"""

# команда /add_admin, проверяет всех пользователей из HOME_GROUP с правами админа
# обновляет этот список в боте, и выводит список всех админов
@owner_router.message(Command("add_admin"))
async def add_admin(message: Message, session: AsyncSession, bot: Bot):
    # Получаем список администраторов текущего чата
    admins = await bot.get_chat_administrators(chat_id=message.chat.id)
    bot.admin_list = [admin.user.id for admin in admins]

    # Обновляем список админов в боте
    id_admins = bot.admin_list

    # Формируем список админов с их именами пользователей
    list_admins = []
    for user in await orm_get_users(session):
        if user.user_id in id_admins:
            await orm_update_status(session, user.user_id, ('admin'))
            list_admins.append(f"• <code>{user.user_id}</code> - @{user.user_name}")

    # Формируем сообщение со списком админов
    admins_text = "\n".join(list_admins)
    await message.answer(f"Администраторы:\n\n{admins_text}")
