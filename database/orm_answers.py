import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debug >>> ')

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Answers


# получаем все ответы юзера
async def orm_get_answer(session: AsyncSession, user_id: int) -> Answers | None:
    query = select(Answers).where(Answers.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()
