import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot

class IsAdminGroupFilter(BaseFilter):
    """
    Фильтр, проверяющий наличие прав администратора в группах
    """
    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def __call__(self, message: Message) -> bool:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.is_chat_admin() == self.is_admin

class IsAdminListFilter(BaseFilter):
    """
    Фильтр, проверяющий наличие прав администратора из составленного списка администраторов
    """
    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def __call__(self, message: Message, bot: Bot) -> bool:
        # Проверяем, находится ли ID пользователя, отправившего сообщение, в списке администраторов
        return (message.from_user.id in bot.admin_list) & self.is_admin
