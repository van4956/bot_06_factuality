import logging

# Инициализируем логгер модуля
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info("Загружен модуль: %s", __name__)

from icecream import ic
ic.configureOutput(includeContext=True, prefix=' >>> Debag >>> ')

from datetime import datetime
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
from database.orm_answers import orm_create_answer, orm_get_current_question, orm_update_current_question, orm_get_result, orm_get_all_results
from database.models import Answers



# Инициализируем роутер уровня модуля
factuality_router = Router()

# Определяем состояния
class TestStates(StatesGroup):
    QUESTION_START = State()
    QUESTION_PROCESS = State()

# Константы для вопросов
QUESTION_1 = __("Вопрос 1:\n\nСколько девочек сегодня оканчивают начальную школу в странах с низким уровнем доходов?")
QUESTION_2 = __("Вопрос 2:\n\nГде живет большая часть населения мира?")
QUESTION_3 = __("Вопрос 3:\n\nЗа последние 20 лет доля мирового населения, живущего в нищете...")
QUESTION_4 = __("Вопрос 4:\n\nКакова сегодня ожидаемая продолжительность жизни в мире?")
QUESTION_5 = __("Вопрос 5:\n\nСегодня в мире насчитывается 2 миллиарда детей в возрасте от 0 до 15 лет. Сколько детей, согласно прогнозу ООН, будет в мире в 2100 году?")
QUESTION_6 = __("Вопрос 6:\n\nПо прогнозам ООН, к 2100 году население земного шара увеличится на 4 миллиарда человек. За счет чего это произойдет?")
QUESTION_7 = __("Вопрос 7:\n\nКак за последние 100 лет изменилось количество смертей в год, вызванных стихийными бедствиями?")
QUESTION_8 = __("Вопрос 8:\n\nСегодня население земного шара составляет около 7 миллиардов человек. Какая карта лучше всего показывает их распределение?\n\n<i>(Карта которая в описании бота ⬆️.\nКаждая фигурка обозначает 1 миллиард человек)</i>")
QUESTION_9 = __("Вопрос 9:\n\nСколько годовалых детей в мире прививается сегодня от каких-либо болезней?")
QUESTION_10 = __("Вопрос 10:\n\nВ среднем по миру к 30 годам мужчины тратят на учебу 10 лет своей жизни. Сколько лет тратят на учебу к тому же возрасту женщины?")
QUESTION_11 = __("Вопрос 11:\n\nВ 1996 году тигры, гигантские панды и черные носороги вошли в список вымирающих видов. Сколько из этих трех видов сегодня находятся под угрозой исчезновения?")
QUESTION_12 = __("Вопрос 12:\n\nСколько человек в мире имеют доступ к электричеству?")
QUESTION_13 = __("Вопрос 13:\n\nЭксперты по глобальному климату считают, что в течение следующих 100 лет средняя температура...")

# Константы для ответов
ANSWER_1_1 = __('1) 20 процентов')
ANSWER_1_2 = __('2) 40 процентов')
ANSWER_1_3 = __('3) 60 процентов')

ANSWER_2_1 = __('1) В странах с низким уровнем доходов')
ANSWER_2_2 = __('2) В странах со средним уровнем доходов')
ANSWER_2_3 = __('3) В странах с высоким уровнем доходов')

ANSWER_3_1 = __('1) ...почти удвоилась')
ANSWER_3_2 = __('2) ...осталась почти неизменной')
ANSWER_3_3 = __('3) ...сократилась почти вдвое')

ANSWER_4_1 = __('1) 50 лет')
ANSWER_4_2 = __('2) 60 лет')
ANSWER_4_3 = __('3) 70 лет')

ANSWER_5_1 = __('1) 4 миллиарда')
ANSWER_5_2 = __('2) 3 миллиарда')
ANSWER_5_3 = __('3) 2 миллиарда')

ANSWER_6_1 = __('1) Будет больше детей (до 15 лет)')
ANSWER_6_2 = __('2) Будет больше взрослых (от 15 до 74 лет)')
ANSWER_6_3 = __('3) Будет больше стариков (от 75 лет)')

ANSWER_7_1 = __('1) Увеличилось более чем в два раза')
ANSWER_7_2 = __('2) Осталось почти неизменным')
ANSWER_7_3 = __('3) Уменьшилось более чем в два раза')

ANSWER_8_1 = __('1) Карта I')
ANSWER_8_2 = __('2) Карта II')
ANSWER_8_3 = __('3) Карта III')

ANSWER_9_1 = __('1) 20 процентов')
ANSWER_9_2 = __('2) 50 процентов')
ANSWER_9_3 = __('3) 80 процентов')

ANSWER_10_1 = __('1) 9 лет')
ANSWER_10_2 = __('2) 6 лет')
ANSWER_10_3 = __('3) 3 года')

ANSWER_11_1 = __('1) Два')
ANSWER_11_2 = __('2) Один')
ANSWER_11_3 = __('3) Ни одного')

ANSWER_12_1 = __('1) 20 процентов')
ANSWER_12_2 = __('2) 50 процентов')
ANSWER_12_3 = __('3) 80 процентов')

ANSWER_13_1 = __('1) ...повысится')
ANSWER_13_2 = __('2) ...останется неизменной')
ANSWER_13_3 = __('3) ...понизится')

# Обновленный словарь
questions_answers = {
    1: (QUESTION_1, {'question1_1': ANSWER_1_1, 'question1_2': ANSWER_1_2, 'question1_3': ANSWER_1_3}),
    2: (QUESTION_2, {'question2_1': ANSWER_2_1, 'question2_2': ANSWER_2_2, 'question2_3': ANSWER_2_3}),
    3: (QUESTION_3, {'question3_1': ANSWER_3_1, 'question3_2': ANSWER_3_2, 'question3_3': ANSWER_3_3}),
    4: (QUESTION_4, {'question4_1': ANSWER_4_1, 'question4_2': ANSWER_4_2, 'question4_3': ANSWER_4_3}),
    5: (QUESTION_5, {'question5_1': ANSWER_5_1, 'question5_2': ANSWER_5_2, 'question5_3': ANSWER_5_3}),
    6: (QUESTION_6, {'question6_1': ANSWER_6_1, 'question6_2': ANSWER_6_2, 'question6_3': ANSWER_6_3}),
    7: (QUESTION_7, {'question7_1': ANSWER_7_1, 'question7_2': ANSWER_7_2, 'question7_3': ANSWER_7_3}),
    8: (QUESTION_8, {'question8_1': ANSWER_8_1, 'question8_2': ANSWER_8_2, 'question8_3': ANSWER_8_3}),
    9: (QUESTION_9, {'question9_1': ANSWER_9_1, 'question9_2': ANSWER_9_2, 'question9_3': ANSWER_9_3}),
    10: (QUESTION_10, {'question10_1': ANSWER_10_1, 'question10_2': ANSWER_10_2, 'question10_3': ANSWER_10_3}),
    11: (QUESTION_11, {'question11_1': ANSWER_11_1, 'question11_2': ANSWER_11_2, 'question11_3': ANSWER_11_3}),
    12: (QUESTION_12, {'question12_1': ANSWER_12_1, 'question12_2': ANSWER_12_2, 'question12_3': ANSWER_12_3}),
    13: (QUESTION_13, {'question13_1': ANSWER_13_1, 'question13_2': ANSWER_13_2, 'question13_3': ANSWER_13_3})
}

# # Словарь вопросов-ответов
# questions_answers = {
#     1: (__("Вопрос 1:\n\nСколько девочек сегодня оканчивают начальную школу в странах с низким уровнем доходов?"),
#         {'question1_1': __('1) 20 процентов'),
#          'question1_2': __('2) 40 процентов'),
#          'question1_3': __('3) 60 процентов')}),
#     2: (__("Вопрос 2:\n\nГде живет большая часть населения мира?"),
#         {'question2_1': __('1) В странах с низким уровнем доходов'),
#          'question2_2': __('2) В странах со средним уровнем доходов'),
#          'question2_3': __('3) В странах с высоким уровнем доходов')}),
#     3: (__("Вопрос 3:\n\nЗа последние 20 лет доля мирового населения, живущего в нищете..."),
#         {'question3_1': __('1) ...почти удвоилась'),
#          'question3_2': __('2) ...осталась почти неизменной'),
#          'question3_3': __('3) ...сократилась почти вдвое')}),
#     4: (__("Вопрос 4:\n\nКакова сегодня ожидаемая продолжительность жизни в мире?"),
#         {'question4_1': __('1) 50 лет'),
#          'question4_2': __('2) 60 лет'),
#          'question4_3': __('3) 70 лет')}),
#     5: (__("Вопрос 5:\n\nСегодня в мире насчитывается 2 миллиарда детей в возрасте от 0 до 15 лет. Сколько детей, согласно прогнозу ООН, будет в мире в 2100 году?"),
#         {'question5_1': __('1) 4 миллиарда'),
#          'question5_2': __('2) 3 миллиарда'),
#          'question5_3': __('3) 2 миллиарда')}),
#     6: (__("Вопрос 6:\n\nПо прогнозам ООН, к 2100 году население земного шара увеличится на 4 миллиарда человек. За счет чего это произойдет?"),
#         {'question6_1': __('1) Будет больше детей (до 15 лет)'),
#          'question6_2': __('2) Будет больше взрослых (от 15 до 74 лет)'),
#          'question6_3': __('3) Будет больше стариков (от 75 лет)')}),
#     7: (__("Вопрос 7:\n\nКак за последние 100 лет изменилось количество смертей в год, вызванных стихийными бедствиями?"),
#         {'question7_1': __('1) Увеличилось более чем в два раза'),
#          'question7_2': __('2) Осталось почти неизменным'),
#          'question7_3': __('3) Уменьшилось более чем в два раза')}),
#     8: (__("Вопрос 8:\n\nСегодня население земного шара составляет около 7 миллиардов человек. Какая карта лучше всего показывает их распределение?\n\n<i>(Карта которая в описании бота ⬆️.\nКаждая фигурка обозначает 1 миллиард человек)</i>"),
#         {'question8_1': __('1) Карта I'),
#          'question8_2': __('2) Карта II'),
#          'question8_3': __('3) Карта III')}),
#     9: (__("Вопрос 9:\n\nСколько годовалых детей в мире прививается сегодня от каких-либо болезней?"),
#         {'question9_1': __('1) 20 процентов'),
#          'question9_2': __('2) 50 процентов'),
#          'question9_3': __('3) 80 процентов')}),
#     10: (__("Вопрос 10:\n\nВ среднем по миру к 30 годам мужчины тратят на учебу 10 лет своей жизни. Сколько лет тратят на учебу к тому же возрасту женщины?"),
#         {'question10_1': __('1) 9 лет'),
#          'question10_2': __('2) 6 лет'),
#          'question10_3': __('3) 3 года')}),
#     11: (__("Вопрос 11:\n\nВ 1996 году тигры, гигантские панды и черные носороги вошли в список вымирающих видов. Сколько из этих трех видов сегодня находятся под угрозой исчезновения?"),
#         {'question11_1': __('1) Два'),
#          'question11_2': __('2) Один'),
#          'question11_3': __('3) Ни одного')}),
#     12: (__("Вопрос 12:\n\nСколько человек в мире имеют доступ к электричеству?"),
#         {'question12_1': __('1) 20 процентов'),
#          'question12_2': __('2) 50 процентов'),
#          'question12_3': __('3) 80 процентов')}),
#     13: (__("Вопрос 13:\n\nЭксперты по глобальному климату считают, что в течение следующих 100 лет средняя температура..."),
#         {'question13_1': __('1) ...повысится'),
#          'question13_2': __('2) ...останется неизменной'),
#          'question13_3': __('3) ...понизится')})
# }

# Словарь правильных ответов (номер вопроса: номер правильного ответа)
correct_answers = {
    1: 3,  # 60 процентов
    2: 2,  # В странах со средним уровнем доходов
    3: 3,  # сократилась почти вдвое
    4: 3,  # 70 лет
    5: 3,  # 2 миллиарда
    6: 2,  # Будет больше взрослых
    7: 3,  # Уменьшилось более чем в два раза
    8: 1,  # Карта I
    9: 3,  # 80 процентов
    10: 1, # 9 лет
    11: 3, # Ни одного
    12: 3, # 80 процентов
    13: 1  # повысится
}

# Функция проверки ответов
async def check_answers(answers_dict: dict) -> int:
    """Функция проверки ответов. Принимает словарь с ответами юзера и возвращает количество правильных ответов. """
    correct_count = 0

    for question_num in range(1, 14):
        # Получаем ответ пользователя из словаря
        user_answer = answers_dict.get(f'answer_{question_num}')
        if user_answer is not None:
            # Преобразуем строку в число, берем последнюю цифру из ответа
            user_answer = int(user_answer)
            # Сравниваем с правильным ответом
            if user_answer == correct_answers[question_num]:
                correct_count += 1

    return correct_count

# Функция расчета общего времени ответов на все вопросы
async def calc_answer_time(answers_dict: dict) -> float:
    """Функция расчета общего времени ответов на все вопросы. Принимает словарь с ответами юзера и возвращает общее время ответов."""
    answer_total_time = 0
    for question_num in range(1, 14):
        answer_time_data = answers_dict.get(f'answer_{question_num}_time')
        if answer_time_data is not None:
            answer_total_time += answer_time_data
    return answer_total_time


# Обработчик инлайн-кнопки "Назад"
@factuality_router.callback_query(F.data == 'back_to_main')
async def factuality_command(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback_query.from_user.id

    # Получаем сохраненный message_id и current_question из FSM
    data = await state.get_data()
    # last_message_id = data.get('last_message_id')
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)

    if current_question == 1:
        new_message = await callback_query.message.edit_text(
            text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                   'Готовы пройти тест?'),
            reply_markup=inline_start_test()) # type: ignore
    elif current_question > 13:
        data = await state.get_data()
        orm_correct_count = await orm_get_result(session, user_id)
        correct_count = data.get('result', orm_correct_count)

        new_message = await callback_query.message.edit_text(
            text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
                   'Вы прошли тест!\n\n'
                   'Ваш результат: {correct_count}/13\n').format(correct_count=correct_count),
            reply_markup=get_callback_btns(btns={_('Правильные ответы'):'correct_answers',
                                                 _('О книге'):'about_book',
                                                 _('О тесте'):'about_test'},
                                                 sizes=(1,1,1))) # type: ignore
    else:
        new_message = await callback_query.message.edit_text(
            text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                   'Вы остановились на {current_question} вопросе. \n\n'
                   'Желаете продолжить тест?').format(current_question=current_question),
            reply_markup=inline_continue_test()) # type: ignore

    # Сохраняем новый (отредактированный) message_id
    await state.update_data(last_message_id=new_message.message_id)
    await callback_query.answer()

# Обработчик инлайн-кнопки "Назад" из donate
@factuality_router.callback_query(F.data == 'donate_back_to_main')
async def donate_back_to_main(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession):
    user_id = callback_query.from_user.id
    # Получаем сохраненный message_id
    data = await state.get_data()
    last_message_id = data.get('last_message_id')

    # Если есть предыдущее сообщение, удаляем его
    if last_message_id:
        try:
            await callback_query.bot.delete_message(chat_id=user_id,
                                                    message_id=last_message_id)
        except Exception as e:
            logger.error("Ошибка при удалении сообщения: %s", e)

    # Получаем результаты теста пользователя из базы
    try:
        orm_correct_count = await orm_get_result(session, user_id)
        correct_count = data.get('result', orm_correct_count)
    except Exception as e:
        logger.error("Ошибка при получении результатов из базы: %s", e)
        correct_count = 0

    new_message = await callback_query.message.answer(
        text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
               'Вы прошли тест!\n\n'
               'Ваш результат: {correct_count}/13\n').format(correct_count=correct_count),
        reply_markup=get_callback_btns(btns={_('Правильные ответы'):'correct_answers',
                                             _('О книге'):'about_book',
                                             _('О тесте'):'about_test'},
                                             sizes=(1,1,1))) # type: ignore
    # Сохраняем новый message_id
    await state.update_data(last_message_id=new_message.message_id)
    await callback_query.answer()

# Обработчик нажатия на инлайн-кнопку "Начать тест", или "Продолжить тест"
@factuality_router.callback_query(F.data.in_(["start_test", "continue_test"]))
async def start_test_callback(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession, workflow_data: dict):
    user_id = callback_query.from_user.id
    data = await state.get_data()
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)
    analytics = workflow_data['analytics']

    question_text = questions_answers[current_question][0]
    question_answers = questions_answers[current_question][1]
    new_message = await callback_query.message.edit_text(
        text=str(question_text),
        reply_markup=get_callback_btns(btns={str(v): k for k, v in question_answers.items()},
                                       sizes=(1,1,1))) # type: ignore
    # Сохраняем новый message_id
    await state.update_data(last_message_id=new_message.message_id)

    # Сохраняем временную метку
    timestamp = datetime.now().timestamp()
    await state.update_data(timestamp=timestamp)

    await state.set_state(TestStates.QUESTION_PROCESS)
    await callback_query.answer()

    await analytics(user_id=user_id,
                    category_name="/process",
                    command_name="/start_test")

# Обработчик для inline ответов на вопросы
@factuality_router.callback_query(StateFilter(TestStates.QUESTION_PROCESS), F.data.startswith('question'))
async def process_question(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession, workflow_data: dict):
    # получаем id юзера, номер вопроса, ответ, сохраняем в FSM
    user_id = callback_query.from_user.id
    data = await state.get_data()
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)
    analytics = workflow_data['analytics']

    timestamp = data.get('timestamp', 0)
    cur_timestamp = datetime.now().timestamp()
    answer_time_data = round(cur_timestamp - timestamp, 2)
    await state.update_data(timestamp=cur_timestamp)

    # проверяем, если текущий вопрос меньше 13, то переходим к следующему вопросу
    if current_question < 13:
        answer_int = 'answer_' + str(current_question)
        answer_data = int(callback_query.data.split('_')[-1])
        answer_int_time = 'answer_' + str(current_question) + '_time'
        answer_dict = {answer_int: answer_data, answer_int_time: answer_time_data}
        await state.update_data(answer_dict)

        # переходим к следующему вопросу, обновляем номер текущего вопроса в FSM
        current_question += 1
        await state.update_data(current_question=current_question)

        # получаем следующий (уже текущий) вопрос, отправляем его юзеру
        question_text = questions_answers[current_question][0]
        question_answers = questions_answers[current_question][1]
        new_message = await callback_query.message.edit_text(
            text=str(question_text),
            reply_markup=get_callback_btns(btns={str(v): k for k, v in question_answers.items()},
                                           sizes=(1,1,1))) # type: ignore

        # Сохраняем новый message_id
        await state.update_data(last_message_id=new_message.message_id)
        await callback_query.answer()

        await analytics(user_id=user_id,
                        category_name="/process",
                        command_name="/process_test")

    # если текущий вопрос больше 13, то завершаем тест
    else:
        answer_int = 'answer_' + str(current_question)
        answer_data = int(callback_query.data.split('_')[-1])
        answer_int_time = 'answer_' + str(current_question) + '_time'
        answer_dict = {answer_int: answer_data, answer_int_time: answer_time_data}
        await state.update_data(answer_dict)

        # обновляем номер текущего вопроса в FSM и в базе, должен быть 14
        current_question += 1
        await state.update_data(current_question=current_question)
        await orm_update_current_question(session, user_id, current_question)

        # получаем все данные из FSM
        data = await state.get_data()

        # оставляем в словаре только ответы и их время
        data_answers = {k: v for k, v in data.items() if k.startswith('answer_') and int(k.split('_')[1]) <= 13}

        # проверяем количество правильных ответов, и добавляем результат к данным для сохранения
        correct_count = await check_answers(data_answers)
        data_answers['result'] = correct_count
        await state.update_data(result=correct_count)
        answer_total_time = await calc_answer_time(data_answers)
        data_answers['answer_total_time'] = answer_total_time

        # сохраняем данные в бд
        try:
            query = update(Answers).where(Answers.user_id == user_id).values(data_answers)
            await session.execute(query)
            await session.commit()
        except Exception as e:
            logger.error("Ошибка при сохранении данных в базу: %s", e)
            await callback_query.message.edit_text(text=_('Ошибка при сохранении данных в базу: %s', e))

        # отправляем юзеру сообщение о завершении теста
        text = _("Тест завершен!\n\n"
                    "Ваш результат: {correct_count}/13").format(correct_count=correct_count)
        new_message = await callback_query.message.edit_text(
            text=str(text),
            reply_markup=get_callback_btns(btns={_('Правильные ответы'):'correct_answers',
                                                 _('О книге'):'about_book',
                                                 _('О тесте'):'about_test'},
                                                 sizes=(1,1,1))) # type: ignore
        # Сохраняем новый message_id
        await state.update_data(last_message_id=new_message.message_id)
        await callback_query.answer()

        await analytics(user_id=user_id,
                        category_name="/process",
                        command_name="/finish_test")

# Обработчик нажатия на инлайн-кнопку "О книге"
@factuality_router.callback_query(F.data == 'about_book')
async def about_book(callback_query: CallbackQuery, state: FSMContext, workflow_data: dict):
    user_id = callback_query.from_user.id

    text = _("📖 О книге «Фактологичность»\n\n"
            "«Фактологичность» – это не просто набор фактов, а итог многолетних исследований Ханса Рослинга, "
            "профессора международного здравоохранения. Автор проводил тесты среди студентов, политиков, ученых и даже нобелевских лауреатов по всему миру.\n\n"
            "Примечательно, что большинство участников, независимо от образования или профессиональной подготовки, "
            "справлялись хуже, чем если бы выбирали ответы случайным образом. Рослинг иллюстрирует это примером обезьяны, "
            "которой предлагалось выбрать один из трех бананов: используя такой подход, она угадала бы 4 из 13 правильных ответов. "
            "Это демонстрирует, что даже эксперты подвержены когнитивным искажениям и стереотипам.\n\n"
            "Ханс Рослинг раскрывает основные инстинкты, заставляющие нас драматизировать мировую ситуацию, и предлагает советы для более рационального мышления.\n\n"
            "Главная идея книги – научиться воспринимать мир через призму фактов, а не догадок.")

    new_message = await callback_query.message.edit_text(
        text=str(text),
        reply_markup=get_callback_btns(btns={_('↩️ Назад'): 'back_to_main'},
                                       sizes=(1,1))) # type: ignore
    await state.update_data(last_message_id=new_message.message_id)
    await callback_query.answer()

    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/info",
                    command_name="/about_book")


# Обработчик нажатия на инлайн-кнопку "О тесте"
@factuality_router.callback_query(F.data == 'about_test')
async def about_test(callback_query: CallbackQuery, state: FSMContext, session: AsyncSession, workflow_data: dict):
    user_id = callback_query.from_user.id

    # получаем все result юзеров
    orm_all_results = [i for i in await orm_get_all_results(session) if i is not None]
    cnt_res = len(orm_all_results) if orm_all_results else 1
    sum_res = sum(orm_all_results) if orm_all_results else 0
    avg_result = sum_res / cnt_res

    text = _("📊 О тесте Factuality Test\n\n"
            "Тест Factuality Test основан на данных, собранных Хансом Рослингом для книги «Фактологичность». "
            "Это инструмент, который показывает, насколько наше восприятие мира искажено стереотипами и когнитивными ошибками.\n\n"
            "Каждый вопрос в тесте выявляет распространённые заблуждения о глобальных тенденциях, таких как уровень бедности, доступ к образованию и здравоохранению. "
            "Результаты участников демонстрируют, как важно основываться на фактах, а не на интуитивных предположениях.\n\n"
            "В процессе создания теста вопросы проверялись на тысячах людей: от студентов и журналистов до политиков и международных экспертов. "
            "Средний результат, полученный авторами книги, составил всего 2-3 правильных ответа из 13, тогда как случайное угадывание дало бы 4. "
            "Это подтверждает влияние мифов и стереотипов на наше мировоззрение.\n\n"
            "На текущий момент:\n"
            "• Количество опрошенных пользователей Factuality Test - {cnt_res}\n"
            "• Средний результат среди опрошенных Factuality Test - {avg_result:.1f}").format(cnt_res=cnt_res, avg_result=avg_result)

    new_message = await callback_query.message.edit_text(
        text=str(text),
        reply_markup=get_callback_btns(btns={_('↩️ Назад'): 'back_to_main'},
                                       sizes=(1,1))) # type: ignore
    await state.update_data(last_message_id=new_message.message_id)
    await callback_query.answer()

    analytics = workflow_data['analytics']
    await analytics(user_id=user_id,
                    category_name="/info",
                    command_name="/about_test")
