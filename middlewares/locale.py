import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from typing import Any
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import TelegramObject
from database.orm_users import orm_get_locale



# Функция для получения user_id из различных типов апдейтов
async def get_user_id(event: TelegramObject) -> int | None:
    """Определяет user_id из различных типов апдейтов"""
    # Обычные сообщения
    if hasattr(event, 'message') and hasattr(event.message, 'from_user'):
        return event.message.from_user.id

    # Callback Query (нажатия на инлайн-кнопки)
    elif hasattr(event, 'callback_query') and hasattr(event.callback_query, 'from_user'):
        return event.callback_query.from_user.id

    # Отредактированные сообщения
    elif hasattr(event, 'edited_message') and hasattr(event.edited_message, 'from_user'):
        return event.edited_message.from_user.id

    # Инлайн запросы (когда бота вызывают в других чатах через @)
    elif hasattr(event, 'inline_query') and hasattr(event.inline_query, 'from_user'):
        return event.inline_query.from_user.id

    # Выбранные инлайн результаты
    elif hasattr(event, 'chosen_inline_result') and hasattr(event.chosen_inline_result, 'from_user'):
        return event.chosen_inline_result.from_user.id

    # Ответы на опросы
    elif hasattr(event, 'poll_answer') and hasattr(event.poll_answer, 'user'):
        return event.poll_answer.user.id

    # Запросы на вступление в чат
    elif hasattr(event, 'chat_join_request') and hasattr(event.chat_join_request, 'from_user'):
        return event.chat_join_request.from_user.id

    # Изменения в участниках чата
    elif hasattr(event, 'chat_member') and hasattr(event.chat_member, 'from_user'):
        return event.chat_member.from_user.id

    # Изменения в моём статусе участника чата
    elif hasattr(event, 'my_chat_member') and hasattr(event.my_chat_member, 'from_user'):
        return event.my_chat_member.from_user.id

    # Предварительная проверка счёта (pre_checkout_query)
    elif hasattr(event, 'pre_checkout_query') and hasattr(event.pre_checkout_query, 'from_user'):
        return event.pre_checkout_query.from_user.id

    # Запрос отправки счёта (shipping_query)
    elif hasattr(event, 'shipping_query') and hasattr(event.shipping_query, 'from_user'):
        return event.shipping_query.from_user.id

    return None



# Класс LocaleFromDBMiddleware, наследуемый от BaseMiddleware, предназначен для определеня локали из бд, и передачи ее в FSMContext
class LocaleFromDBMiddleware(BaseMiddleware):
    def __init__(self, workflow_data: dict):
        super().__init__()
        self.workflow_data = workflow_data
        logger.info("class LocaleFromDBMiddleware __init__")

    async def __call__(self, handler, event: TelegramObject, data: dict) -> Any:
        try:
            # Добавляем workflow_data в data
            if not data.get("workflow_data"):
                data["workflow_data"] = self.workflow_data

                # Получаем функцию analytics из workflow_data
                analytics = self.workflow_data.get("analytics")

                # Получаем ID пользователя
                user_id = await get_user_id(event)
                user_id=user_id if user_id else 0000000000000
                # ic(user_id)

                if analytics:
                    # Отправляем пинг по всем апдейтам в InfluxDB
                    # Если событие от пользователя, используем user_id
                    # для неопознанных используем ID 0000000000000
                    await analytics(user_id=user_id,
                                    category_name="middleware",
                                    command_name="ping")
                    # logger.info("Отправлен пинг в InfluxDB =========================")

            # Находим локаль в FSM
            fsm_context = data.get("state")
            fsm_data = await fsm_context.get_data()
            current_locale = fsm_data.get("locale")

            # Если локаль уже есть в FSM, передаем обработку дальше
            if current_locale:
                return await handler(event, data)

            # Если локаль не найдена, получаем сессию БД
            session = data.get("session")
            if not session:
                logger.error("Сессия БД не найдена в middleware - LocaleFromDBMiddleware.")
                return await handler(event, data)

            # Проверяем, является ли событие сообщением от пользователя
            if hasattr(event, 'message') and hasattr(event.message, 'from_user'):
                user_id = event.message.from_user.id
                locale = await orm_get_locale(session, user_id)

                # Если локаль найдена в бд, отправляем ее в FSMContext
                if locale:
                    logger.info("Установлена локаль '%s' для пользователя %s", locale, user_id)
                    await fsm_context.update_data(locale=locale)

            # Передаем обработку дальше
            return await handler(event, data)

        except Exception as e:
            logger.error("Ошибка в middleware LocaleFromDBMiddleware: %s", str(e))
            return await handler(event, data)