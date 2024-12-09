import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message

class ChatTypeFilter(BaseFilter):
    """
    Фильтр для фильтрации сообщений по типу чата.
    Позволяет указать конкретный тип чата (например, 'private', 'group') или список типов чатов.
    """
    def __init__(self, chat_type: Union[str, list]):
        self.chat_type = chat_type

    async def __call__(self, message: Message) -> bool:
        if isinstance(self.chat_type, str):
            return message.chat.type == self.chat_type
        else:
            return message.chat.type in self.chat_type
