import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from aiogram.filters import BaseFilter
from aiogram.types import Message

class MemberCanRestrictFilter(BaseFilter):
    """
    Фильтр для проверки, может ли участник чата ограничивать других участников.
    Этот фильтр используется для ограничения выполнения команд в зависимости от прав участника на ограничение других пользователей.
    """
    def __init__(self, member_can_restrict: bool):
        """
        Инициализация фильтра с флагом проверки возможности ограничений.
        member_can_restrict: Флаг, указывающий, может ли участник ограничивать других (True или False).
        """
        self.member_can_restrict = member_can_restrict

    async def __call__(self, message: Message) -> bool:
        """
        Проверка, имеет ли участник чата права на ограничение других пользователей.
        :param message: Объект сообщения из aiogram.
        :return: True, если участник может ограничивать других, иначе False.
        """
        # Получение информации о пользователе в чате
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)

        # Проверка прав: если пользователь является создателем чата или имеет права на ограничение участников
        # Telegram считает, что создатель чата не может ограничивать участников, поэтому добавляем проверку
        return (member.is_chat_creator() or member.can_restrict_members) == self.member_can_restrict
