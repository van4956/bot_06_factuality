import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder



# Инициализируем роутер уровня модуля
group_router = Router()
group_router.message.filter(F.chat.type == "group")


# Удаляем сообщение о присоединении или выходе участника из группы
@group_router.message(F.content_type.in_({'new_chat_members', 'left_chat_member'}))
async def on_user_join_or_left(message: Message):
    """
    Обработчик для удаления сообщений о присоединении или выходе участников из группы.
    Telegram не отправляет обновления 'left_chat_member', когда в группе более 50 участников,
    в таких случаях можно использовать https://core.telegram.org/bots/api#chatmemberupdated.
    :param message: Сервисное сообщение о присоединении или выходе участника.
    """
    await message.delete()

 # добавить суперСпам фильтр сообщений ХоудиХо
