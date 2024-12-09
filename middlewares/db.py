import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker


# Класс DataBaseSession, наследуемый от BaseMiddleware, предназначен для работы с сессиями базы данных
class DataBaseSession(BaseMiddleware):
    # принимаем пул сессий async_sessionmaker
    def __init__(self, session_pool: async_sessionmaker):
        self.session_pool = session_pool  # Сохраняем пул сессий для дальнейшего использования
        logger.info("class DataBaseSession __init__")

    # Асинхронный вызов промежуточного обработчика
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],  # Обработчик событий
        event: TelegramObject,  # Событие в Telegram (например, сообщение)
        data: Dict[str, Any],  # Словарь с данными, ассоциированными с событием
        ) -> Any:

        # logger.info("class DataBaseSession __call__")

        # Создание асинхронной сессии с базой данных
        async with self.session_pool() as session:
            data['session'] = session  # Добавляем сессию в словарь данных
            return await handler(event, data)  # Вызываем следующий обработчик с обновленными данными
