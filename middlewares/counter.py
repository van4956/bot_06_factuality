import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class CounterMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.counter = 0
        logger.info("class CounterMiddleware __init__")

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject, data: Dict[str, Any]) -> Any:
        # logger.info("class CounterMiddleware __call__")

        self.counter += 1
        data['counter'] = self.counter
        
        return await handler(event, data)
