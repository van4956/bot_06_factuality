import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram import Bot



class IsOwnerFilter(BaseFilter):
    """
    Фильтр, проверяет является ли пользователь владельцем бота.
    Принимает параметр is_owner: true/false.
    Возвращает True, если пользователь в списке владельцев.
    """
    def __init__(self, is_owner: bool):
        self.is_owner = is_owner

    async def __call__(self, message: Message, bot: Bot) -> bool:

        # Проверяем, находится ли ID пользователя, отправившего сообщение, в списке владельцев
        return (message.from_user.id in bot.owner) & self.is_owner
