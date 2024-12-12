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
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from sqlalchemy import update

from common.keyboard import get_callback_btns, inline_start_test, inline_continue_test
from database.orm_answers import orm_create_answer, orm_get_current_question, orm_update_current_question
from database.models import Answers



# Инициализируем роутер уровня модуля
factuality_router = Router()

# Определяем состояния
class TestStates(StatesGroup):
    QUESTION_START = State()
    QUESTION_PROCESS = State()

# словарь вопросов-ответов
questions_answers = {
    1: ("Вопрос 1: Какой-то текст вопроса...", {'question1_1': 'Ответ 1-1', 'question1_2': 'Ответ 1-2', 'question1_3': 'Ответ 1-3'}),
    2: ("Вопрос 2: Какой-то текст вопроса...", {'question2_1': 'Ответ 2-1', 'question2_2': 'Ответ 2-2', 'question2_3': 'Ответ 2-3'}),
    3: ("Вопрос 3: Какой-то текст вопроса...", {'question3_1': 'Ответ 3-1', 'question3_2': 'Ответ 3-2', 'question3_3': 'Ответ 3-3'}),
    4: ("Вопрос 4: Какой-то текст вопроса...", {'question4_1': 'Ответ 4-1', 'question4_2': 'Ответ 4-2', 'question4_3': 'Ответ 4-3'}),
    5: ("Вопрос 5: Какой-то текст вопроса...", {'question5_1': 'Ответ 5-1', 'question5_2': 'Ответ 5-2', 'question5_3': 'Ответ 5-3'}),
    6: ("Вопрос 6: Какой-то текст вопроса...", {'question6_1': 'Ответ 6-1', 'question6_2': 'Ответ 6-2', 'question6_3': 'Ответ 6-3'}),
    7: ("Вопрос 7: Какой-то текст вопроса...", {'question7_1': 'Ответ 7-1', 'question7_2': 'Ответ 7-2', 'question7_3': 'Ответ 7-3'}),
    8: ("Вопрос 8: Какой-то текст вопроса...", {'question8_1': 'Ответ 8-1', 'question8_2': 'Ответ 8-2', 'question8_3': 'Ответ 8-3'}),
    9: ("Вопрос 9: Какой-то текст вопроса...", {'question9_1': 'Ответ 9-1', 'question9_2': 'Ответ 9-2', 'question9_3': 'Ответ 9-3'}),
    10: ("Вопрос 10: Какой-то текст вопроса...", {'question10_1': 'Ответ 10-1', 'question10_2': 'Ответ 10-2', 'question10_3': 'Ответ 10-3'}),
    11: ("Вопрос 11: Какой-то текст вопроса...", {'question11_1': 'Ответ 11-1', 'question11_2': 'Ответ 11-2', 'question11_3': 'Ответ 11-3'}),
    12: ("Вопрос 12: Какой-то текст вопроса...", {'question12_1': 'Ответ 12-1', 'question12_2': 'Ответ 12-2', 'question12_3': 'Ответ 12-3'}),
    13: ("Вопрос 13: Какой-то текст вопроса...", {'question13_1': 'Ответ 13-1', 'question13_2': 'Ответ 13-2', 'question13_3': 'Ответ 13-3'})
}

# Обработчик инлайн-кнопки "Назад"
@factuality_router.callback_query(F.data == 'back_to_main')
async def factuality_command(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback_query.from_user.id

    # Получаем сохраненный message_id и current_question из FSM
    data = await state.get_data()
    last_message_id = data.get('last_message_id')
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)

    if current_question == 1:
        new_message = await callback_query.message.edit_text(text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                                    'Готовы пройти тест?'),
                                reply_markup=inline_start_test()) # type: ignore
    elif current_question > 13:
        new_message = await callback_query.message.edit_text(text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                                    'Вы уже прошли тест!\n'
                                    'Описываем какой то результат'))
    else:
        new_message = await callback_query.message.edit_text(text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                                    'Вы остановились на {current_question} вопросе. \n'
                                    'Желаете продолжить тест?').format(current_question=current_question),
                                reply_markup=inline_continue_test()) # type: ignore

    # Сохраняем новый (отредактированный) message_id
    await state.update_data(last_message_id=new_message.message_id)
    await callback_query.answer()

# Обработчик нажатия на инлайн-кнопку "Начать тест", или "Продолжить тест"
@factuality_router.callback_query(F.data.in_(["start_test", "continue_test"]))
async def start_test_callback(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback_query.from_user.id
    data = await state.get_data()
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)

    question_text = questions_answers[current_question][0]
    question_answers = questions_answers[current_question][1]
    new_message = await callback_query.message.edit_text(text=_(question_text),
                                            reply_markup=get_callback_btns(btns={v: k for k, v in question_answers.items()}, sizes=(1,1,1))) # type: ignore
    # Сохраняем новый message_id
    await state.update_data(last_message_id=new_message.message_id)

    await state.set_state(TestStates.QUESTION_PROCESS)
    await callback_query.answer()

# Обработчик для inline ответов на вопросы
@factuality_router.callback_query(StateFilter(TestStates.QUESTION_PROCESS), F.data.startswith('question'))
async def process_question(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    # получаем id юзера, номер вопроса, ответ, сохраняем в FSM
    user_id = callback_query.from_user.id
    data = await state.get_data()
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)

    # проверяем, если текущий вопрос меньше 13, то переходим к следующему вопросу
    if current_question < 13:
        answer_int = 'answer_' + str(current_question)
        answer_data = callback_query.data.split('_')[-1]
        answer_dict = {answer_int: answer_data}
        await state.update_data(answer_dict)

        # переходим к следующему вопросу, обновляем номер текущего вопроса в FSM
        current_question += 1
        await state.update_data(current_question=current_question)

        # получаем следующий (уже текущий) вопрос, отправляем его юзеру
        question_text = questions_answers[current_question][0]
        question_answers = questions_answers[current_question][1]
        new_message = await callback_query.message.edit_text(text=_(question_text),
                                            reply_markup=get_callback_btns(btns={v: k for k, v in question_answers.items()}, sizes=(1,1,1))) # type: ignore

        # Сохраняем новый message_id
        await state.update_data(last_message_id=new_message.message_id)
        await callback_query.answer()
    else:
        answer_int = 'answer_' + str(current_question)
        answer_data = callback_query.data.split('_')[-1]
        answer_dict = {answer_int: answer_data}
        await state.update_data(answer_dict)

        # обновляем номер текущего вопроса в FSM и в базе, должен быть 14
        current_question += 1
        await state.update_data(current_question=current_question)
        await orm_update_current_question(session, user_id, current_question)

        # получаем все ответы из FSM и сохраняем в базу
        data = await state.get_data()

        # оставляем в словаре только ответы
        data = {k: v for k, v in data.items() if k.startswith('answer_')}
        query = update(Answers).where(Answers.user_id == user_id).values(data)
        await session.execute(query)
        await session.commit()

        # отправляем юзеру сообщение о завершении теста
        text = _("Тест завершен!\n\n"
                    "Базовый результат:\n"
                    "- Количество правильных ответов ...\n"
                    "- Краткое сравнение с выборкой автора ...")
        new_message = await callback_query.message.edit_text(text=text,
                                            reply_markup=get_callback_btns(btns={'Правильные ответы':'correct_answers',
                                                                                 'Больше о книге':'book_info',
                                                                                 'Статистика теста':'test_stats'},
                                                                        sizes=(1,1,1))) # type: ignore
        # Сохраняем новый message_id
        await state.update_data(last_message_id=new_message.message_id)
        await callback_query.answer()
