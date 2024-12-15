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

# создаем запись в таблице answers
async def orm_create_answer(session: AsyncSession, user_id: int) -> None:
    new_answer = Answers(user_id=user_id, current_question=1)
    session.add(new_answer)
    await session.commit()

# получаем все ответы юзера
async def orm_get_answer(session: AsyncSession, user_id: int) -> Answers | None:
    query = select(Answers).where(Answers.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

# получаем текущий вопрос юзера
async def orm_get_current_question(session: AsyncSession, user_id: int) -> int | None:
    query = select(Answers.current_question).where(Answers.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

# обновляем текущий вопрос юзера
async def orm_update_current_question(session: AsyncSession, user_id: int, question_int: int) -> None:
    query = update(Answers).where(Answers.user_id == user_id).values(current_question=question_int)
    await session.execute(query)
    await session.commit()

# получаем количество правильных ответов юзера
async def orm_get_result(session: AsyncSession, user_id: int) -> int | None:
    query = select(Answers.result).where(Answers.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

# получаем все result юзеров
async def orm_get_all_results(session: AsyncSession) -> list[int]:
    query = select(Answers.result)
    result = await session.execute(query)
    return result.scalars().all()
