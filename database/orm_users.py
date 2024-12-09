import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debug >>> ')

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Users



# получаем id всеx юзеров находящиеся в бд
async def orm_get_ids(session: AsyncSession):
    query = select(Users.user_id)
    result = await session.execute(query)
    return result.scalars().all()

# добавляем одного юзера в бд
async def orm_add_user(session: AsyncSession, data: dict):
    # создаем объект Users, передаем ему данные из data
    obj = Users(user_id=data["user_id"],
                user_name=data["user_name"],
                full_name=data["full_name"],
                locale=data['locale'],
                status=data['status'],
                flag=data['flag'],
                )
    list_user_ids = [user_id for user_id in await orm_get_ids(session)]

    # добавляем объект Users в сессию, если такого еще не было
    if data["user_id"] not in list_user_ids:
        session.add(obj)
    await session.commit() # закрепляем данные в базе данных

# получаем всеx юзеров находящиеся в бд
async def orm_get_users(session: AsyncSession):
    query = select(Users)
    result = await session.execute(query)
    return result.scalars().all()

# получаем одного юзера по его user_id
async def orm_get_user(session: AsyncSession, user_id: int):
    query = select(Users).where(Users.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

# получаем локаль юзера по user_id
async def orm_get_locale(session: AsyncSession, user_id: int):
    query = select(Users.locale).where(Users.user_id == user_id)
    result = await session.execute(query)
    return result.scalar()

# изменение статуса юзера
async def orm_update_status(session: AsyncSession, user_id: int, data):
    query = update(Users).where(Users.user_id == user_id).values(status=data)
    await session.execute(query)
    await session.commit()

# изменение locale юзера
async def orm_update_locale(session: AsyncSession, user_id: int, data):
    query = update(Users).where(Users.user_id == user_id).values(locale=data)
    await session.execute(query)
    await session.commit()
