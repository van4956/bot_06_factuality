import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from sqlalchemy import DateTime, Float, String, Text, Integer, func, BigInteger, ForeignKey, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    '''первичный класс, от него дальше будут наследоваться все остальные'''
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Users(Base):
    '''class Users соответствует таблице users в базе данных'''
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_name: Mapped[str] = mapped_column(String(150), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    locale: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(150), nullable=False)
    flag: Mapped[int] = mapped_column(Integer, nullable=False)  # тротлинг

class Answers(Base):
    '''class Answers соответствует таблице answers в базе данных'''
    __tablename__ = "answers"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True, autoincrement=True)
    current_question: Mapped[int] = mapped_column(Integer, nullable=False)
    answer_1: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_1_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_2: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_2_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_3: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_3_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_4: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_4_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_5: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_5_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_6: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_6_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_7: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_7_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_8: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_8_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_9: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_9_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_10: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_10_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_11: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_11_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_12: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_12_time: Mapped[Float] = mapped_column(Float, nullable=True)
    answer_13: Mapped[int] = mapped_column(Integer, nullable=True)
    answer_13_time: Mapped[Float] = mapped_column(Float, nullable=True)
    result: Mapped[int] = mapped_column(Integer, CheckConstraint('result >= 0 AND result <= 13'),nullable=True)
    total_time: Mapped[Float] = mapped_column(Float, nullable=True)
