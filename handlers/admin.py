import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from filters.is_admin import IsAdminListFilter
from filters.chat_type import ChatTypeFilter

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdminListFilter(is_admin=True))

# секретный хендлер, покажет содержимое data пользователя
@admin_router.message(F.text == "..")
async def data_cmd(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer(str(data))
