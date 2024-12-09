import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from aiogram import Router, F, Bot
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.i18n import gettext as _

from database.orm_users import orm_update_locale
from common import keyboard

# Инициализируем роутер уровня модуля
other_router = Router()



# Клавиатура выбора языка
def keyboard_language():
    button_1 = InlineKeyboardButton(text=_('🇺🇸 Английский'), callback_data='locale_en')
    button_2 = InlineKeyboardButton(text=_('🇷🇺 Русский'), callback_data='locale_ru')
    button_3 = InlineKeyboardButton(text=_('🇩🇪 Немецкий'), callback_data='locale_de')
    # button_4 = InlineKeyboardButton(text=_('🇫🇷 Французский'), callback_data='locale_fr')
    # button_5 = InlineKeyboardButton(text=_('🇯🇵 Японский'), callback_data='locale_ja')

    return InlineKeyboardMarkup(inline_keyboard=[[button_1], [button_2], [button_3]])


# Это хендлер будет срабатывать на команду locale
@other_router.message(Command('language'))
async def locale_cmd(message: Message):
    await message.answer(_("Настройки языка"), reply_markup=keyboard.del_kb)
    await message.answer(text=_('Выберите язык'),
                         reply_markup=keyboard_language())


@other_router.callback_query(F.data.startswith("locale_"))
async def update_locale_cmd(callback: CallbackQuery, session: AsyncSession, state: FSMContext, workflow_data: dict):
    user_id = callback.from_user.id

    if callback.data == 'locale_en':
        await orm_update_locale(session, user_id, 'en')  # Обновляем локаль в бд
        await state.update_data(locale='en')  # Обновляем локаль в контексте
        await callback.message.edit_text('Choose a language ', reply_markup=None)  # Редактируем сообщение, скрываем inline клавиатуру
        await callback.answer("Selected: 🇺🇸 English")  # Отправляем всплывашку
        await callback.message.answer("Current language \n\n 🇺🇸 English") # Отправляем новое сообщение

    elif callback.data == 'locale_ru':
        await orm_update_locale(session, user_id, 'ru')  # Обновляем локаль в бд
        await state.update_data(locale='ru')  # Обновляем локаль в контексте
        await callback.message.edit_text('Выберите язык ', reply_markup=None)   # Редактируем сообщение, скрываем inline клавиатуру
        await callback.answer("Выбран: 🇷🇺 Русский язык")  # Отправляем всплывашку
        await callback.message.answer("Текущий язык \n\n 🇷🇺 Русский") # Отправляем новое сообщение

    elif callback.data == 'locale_de':
        await orm_update_locale(session, user_id, 'de')  # Обновляем локаль в бд
        await state.update_data(locale='de')  # Обновляем локаль в контексте
        await callback.message.edit_text('Wählen Sie eine Sprache ', reply_markup=None)  # type: ignore # Редактируем сообщение,скрываем клавиатуру
        await callback.answer("Ausgewählt 🇩🇪 Deutsch")  # Отправляем всплывашку
        await callback.message.answer("Aktuelle Sprache \n\n 🇩🇪 Deutsch")   # Отправляем новое сообщение

    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/options",
                    command_name="/language")


# хендлер на команду /information
@other_router.message(Command('information'))
async def information_cmd(message: Message, workflow_data: dict):
    await message.answer(text=_('📚 О боте Factuality Test\n\n'
                                'Этот бот создан на основе книги "Фактологичность" Ханса Рослинга, '
                                'профессора международного здравоохранения и известного спикера TED.\n\n'
                                '🎯 Что делает бот:\n'
                                '• Проводит тест из 13 вопросов о глобальных тенденциях\n'
                                '• Сравнивает ваши результаты с тысячами других участников\n'
                                '• Помогает увидеть распространённые заблуждения о современном мире\n\n'
                                '📊 Интересный факт: В среднем люди отвечают правильно примерно на 2-3 вопроса из 13. '
                                'Сможете ли вы сделать лучше?\n\n'
                                '🤔 Почему это важно?\n'
                                'Понимание реального состояния мира помогает принимать более взвешенные решения '
                                'и избегать распространённых когнитивных искажений.\n\n'
                                'Используйте /factuality чтобы начать тест!'))

    user_id = message.from_user.id
    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/options",
                    command_name="/information")


# хендлер на команду /terms
@other_router.message(Command('terms'))
async def terms_cmd(message: Message, workflow_data: dict):
    await message.answer(text=_('📋 Условия использования Factuality Test\n\n'
                                'Используя этого бота, вы соглашаетесь со следующими условиями:\n\n'
                                '📊 Сбор данных:\n'
                                '• Мы сохраняем ваши ответы на вопросы теста\n'
                                '• Собираем базовую информацию профиля (имя пользователя, язык)\n'
                                '• Анализируем агрегированную статистику прохождения теста\n\n'
                                '🔒 Конфиденциальность:\n'
                                '• Все данные анонимизированы\n'
                                '• Мы не передаем персональные данные третьим лицам\n'
                                '• Используем информацию только для улучшения работы бота\n\n'
                                '❌ Отказ от использования:\n'
                                '• Чтобы остановить бота, используйте команду /stop\n'
                                '• Или заблокируйте бота стандартными средствами Telegram\n'
                                '• При этом ваши данные будут удалены из базы\n\n'
                                'По всем вопросам: @van4956'))

    user_id = message.from_user.id
    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/options",
                    command_name="/terms")
