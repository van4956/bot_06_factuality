import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message
from cachetools import TTLCache

# Создаём кэш для троттлинга
cache = TTLCache(maxsize=float('inf'),  # неограниченное количество пользователей в кэше
                 ttl=0.5  # время хранения каждого пользователя в кэше (0.5 секунды)
                 )

# Мидлварь для троттлинга (отслеживание чрезмерных действий пользователей)
class ThrottleMiddleware(BaseMiddleware):
    """
    Мидлварь для троттлинга (отслеживание чрезмерных действий пользователей)
    """
    def __init__(self) -> None:
        super().__init__()
        logger.info("class ThrottleMiddleware __init__")

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict[str, Any]) -> Any:
        try:
            user_id = None

            # Проверяем, является ли событие сообщением от пользователя
            if hasattr(event, 'message') and hasattr(event.message, 'from_user'):
                user_id = event.message.from_user.id
                # logger.info(f"class ThrottleMiddleware  -  User {user_id} -> Message")

            # Проверяем, является ли событие CallbackQuery (инлайн кнопка) от пользователя
            if hasattr(event, 'callback_query') and hasattr(event.callback_query, 'from_user'):
                user_id = event.callback_query.from_user.id
                # logger.info(f"class ThrottleMiddleware  -  User {user_id} -> CallbackQuery")

            # Если user_id найден и он уже в кэше (значит действие недавно уже выполнялось)
            if user_id is not None:
                if cache.get(user_id):
                    logger.info(f"class ThrottleMiddleware  -  User {user_id} -> Blocked")
                    return

                # Если пользователь не в кэше, добавляем его туда
                cache[user_id] = True

            # Передаём управление следующему обработчику
            return await handler(event, data)

        except Exception as e:
            logger.exception("Ошибка в middleware ThrottleMiddleware: %s", str(e))
            return await handler(event, data)
