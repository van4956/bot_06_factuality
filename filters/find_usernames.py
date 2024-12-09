import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from typing import Union, Dict, Any

from aiogram.filters import BaseFilter
from aiogram.types import Message

class HasUsernamesFilter(BaseFilter):
    """
    Кастомный фильтр для aiogram, который проверяет наличие упоминаний (@username) в сообщении.
    Если упоминания найдены, они передаются в обработчик в виде словаря с ключом "usernames".
    """
    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        """
        Проверка на наличие упоминаний в сообщении и их извлечение.
        :param message: Объект сообщения из aiogram.
        :return: Словарь с ключом "usernames" и найденными именами пользователей, если они есть, иначе False.
        """
        # Если нет никаких entities (например, упоминаний, ссылок и т.д.), вернется None,
        # в таком случае считаем, что это пустой список
        entities = message.entities or []

        # Проверяем на наличие упоминаний пользователей (@username) и извлекаем их из текста
        # с использованием метода extract_from().
        found_usernames = [item.extract_from(message.text) for item in entities if item.type == "mention"]

        # Если найдены имена пользователей, возвращаем их в виде словаря с ключом "usernames"
        if len(found_usernames) > 0:
            return {"usernames": found_usernames}

        # Если упоминаний пользователей не найдено, возвращаем False
        return False
