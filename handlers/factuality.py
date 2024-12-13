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


# Словарь вопросов-ответов
questions_answers = {
    1: ("Вопрос 1:\n\nСколько девочек сегодня оканчивают начальную школу в странах с низким уровнем доходов?",
        {'question1_1': '1) 20 процентов',
         'question1_2': '2) 40 процентов',
         'question1_3': '3) 60 процентов'}),
    2: ("Вопрос 2:\n\nГде живет большая часть населения мира?",
        {'question2_1': '1) В странах с низким уровнем доходов',
         'question2_2': '2) В странах со средним уровнем доходов',
         'question2_3': '3) В странах с высоким уровнем доходов'}),
    3: ("Вопрос 3:\n\nЗа последние 20 лет доля мирового населения, живущего в нищете...",
        {'question3_1': '1) ...почти удвоилась',
         'question3_2': '2) ...осталась почти неизменной',
         'question3_3': '3) ...сократилась почти вдвое'}),
    4: ("Вопрос 4:\n\nКакова сегодня ожидаемая продолжительность жизни в мире?",
        {'question4_1': '1) 50 лет',
         'question4_2': '2) 60 лет',
         'question4_3': '3) 70 лет'}),
    5: ("Вопрос 5:\n\nСегодня в мире насчитывается 2 миллиарда детей в возрасте от 0 до 15 лет. Сколько детей, согласно прогнозу ООН, будет в мире в 2100 году?",
        {'question5_1': '1) 4 миллиарда',
         'question5_2': '2) 3 миллиарда',
         'question5_3': '3) 2 миллиарда'}),
    6: ("Вопрос 6:\n\nПо прогнозам ООН, к 2100 году население земного шара увеличится на 4 миллиарда человек. За счет чего это произойдет?",
        {'question6_1': '1) Будет больше детей (до 15 лет)',
         'question6_2': '2) Будет больше взрослых (от 15 до 74 лет)',
         'question6_3': '3) Будет больше стариков (от 75 лет)'}),
    7: ("Вопрос 7:\n\nКак за последние 100 лет изменилось количество смертей в год, вызванных стихийными бедствиями?",
        {'question7_1': '1) Увеличилось более чем в два раза',
         'question7_2': '2) Осталось почти неизменным',
         'question7_3': '3) Уменьшилось более чем в два раза'}),
    8: ("Вопрос 8:\n\nСегодня население земного шара составляет около 7 миллиардов человек. Какая карта лучше всего показывает их распределение?\n\n<i>(Карта которая в описании бота ⬆️. Каждая фигурка обозначает 1 миллиард человек)</i>",
        {'question8_1': '1) Карта А',
         'question8_2': '2) Карта Б',
         'question8_3': '3) Карта В'}),
    9: ("Вопрос 9:\n\nСколько годовалых детей в мире прививается сегодня от каких-либо болезней?",
        {'question9_1': '1) 20 процентов',
         'question9_2': '2) 50 процентов',
         'question9_3': '3) 80 процентов'}),
    10: ("Вопрос 10:\n\nВ среднем по миру к 30 годам мужчины тратят на учебу 10 лет своей жизни. Сколько лет тратят на учебу к тому же возрасту женщины?",
        {'question10_1': '1) 9 лет',
         'question10_2': '2) 6 лет',
         'question10_3': '3) 3 года'}),
    11: ("Вопрос 11:\n\nВ 1996 году тигры, гигантские панды и черные носороги вошли в список вымирающих видов. Сколько из этих трех видов сегодня находятся под угрозой исчезновения?",
        {'question11_1': '1) Два',
         'question11_2': '2) Один',
         'question11_3': '3) Ни одного'}),
    12: ("Вопрос 12:\n\nСколько человек в мире имеют доступ к электричеству?",
        {'question12_1': '1) 20 процентов',
         'question12_2': '2) 50 процентов',
         'question12_3': '3) 80 процентов'}),
    13: ("Вопрос 13:\n\nЭксперты по глобальному климату считают, что в течение следующих 100 лет средняя температура...",
        {'question13_1': '1) ...повысится',
         'question13_2': '2) ...останется неизменной',
         'question13_3': '3) ...понизится'})
}

# Словарь правильных ответов (номер вопроса: номер правильного ответа)
correct_answers = {
    1: 3,  # 60 процентов
    2: 2,  # В странах со средним уровнем доходов
    3: 3,  # сократилась почти вдвое
    4: 3,  # 70 лет
    5: 3,  # 2 миллиарда
    6: 2,  # Будет больше взрослых
    7: 3,  # Уменьшилось более чем в два раза
    8: 1,  # Карта А
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
    last_message_id = data.get('last_message_id')
    orm_current_question = await orm_get_current_question(session, user_id)
    current_question = data.get('current_question', orm_current_question)

    if current_question == 1:
        new_message = await callback_query.message.edit_text(text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                                    'Готовы пройти тест?'),
                                reply_markup=inline_start_test()) # type: ignore
    elif current_question > 13:
        data = await state.get_data()
        orm_correct_count = await orm_get_result(session, user_id)
        correct_count = data.get('result', orm_correct_count)
        orm_all_results = await orm_get_all_results(session)
        cnt = len(orm_all_results) if orm_all_results else 1
        avg_result = sum(orm_all_results) / cnt
        new_message = await callback_query.message.edit_text(text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
                                    'Вы уже прошли тест!\n\n'
                                    'Ваш результат: {correct_count}/13\n'
                                    'Ср.результат бота: {avg_result}/13\n'
                                    'Ср.результат книги: 2.2/13').format(correct_count=correct_count, avg_result=avg_result),
                                    reply_markup=get_callback_btns(btns={'Правильные ответы':'correct_answers',
                                                                        'Больше о книге':'book_info',
                                                                        'Статистика теста':'test_stats'},
                                                                        sizes=(1,1,1))) # type: ignore
    else:
        new_message = await callback_query.message.edit_text(text=_('Factuality Test.\nТест по книге Ганса Рослинга «Фактологичность»\n\n'
                                    'Вы остановились на {current_question} вопросе. \n'
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

    try:
        orm_correct_count = await orm_get_result(session, user_id)
        correct_count = data.get('result', orm_correct_count)
        orm_all_results = await orm_get_all_results(session)
        cnt_res = len(orm_all_results) if orm_all_results else 1
        sum_res = sum(orm_all_results) if orm_all_results else 0
        avg_result = sum_res / cnt_res
    except Exception as e:
        logger.error("Ошибка при получении результатов из базы: %s", e)
        correct_count = 0
        avg_result = 0

    new_message = await callback_query.message.answer(text=_('Factuality Test.\nТест по книге Ханса Рослинга «Фактологичность»\n\n'
                                'Вы уже прошли тест!\n\n'
                                'Ваш результат: {correct_count}/13\n'
                                'Ср.результат бота: {avg_result}/13\n'
                                'Ср.результат книги: 2.2/13').format(correct_count=correct_count, avg_result=avg_result),
                                reply_markup=get_callback_btns(btns={'Правильные ответы':'correct_answers',
                                                                    'Больше о книге':'book_info',
                                                                    'Статистика теста':'test_stats'},
                                                                    sizes=(1,1,1))) # type: ignore
    # Сохраняем новый message_id
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

    # Сохраняем временную метку
    timestamp = datetime.now().timestamp()
    # ic(timestamp)
    await state.update_data(timestamp=timestamp)

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

    timestamp = data.get('timestamp', 0)
    cur_timestamp = datetime.now().timestamp()
    answer_time_data = round(cur_timestamp - timestamp, 2)
    await state.update_data(timestamp=cur_timestamp)
    # ic(answer_time_data)

    # проверяем, если текущий вопрос меньше 13, то переходим к следующему вопросу
    if current_question < 13:
        answer_int = 'answer_' + str(current_question)
        answer_data = callback_query.data.split('_')[-1]
        answer_int_time = 'answer_' + str(current_question) + '_time'
        answer_dict = {answer_int: answer_data, answer_int_time: answer_time_data}
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

    # если текущий вопрос больше 13, то завершаем тест
    else:
        answer_int = 'answer_' + str(current_question)
        answer_data = callback_query.data.split('_')[-1]
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
        # ic(data_answers)

        # сохраняем данные в бд
        try:
            query = update(Answers).where(Answers.user_id == user_id).values(data_answers)
            await session.execute(query)
            await session.commit()
        except Exception as e:
            logger.error("Ошибка при сохранении данных в базу: %s", e)
            await callback_query.message.edit_text(text=_('Ошибка при сохранении данных в базу: %s', e))

        # получаем все result юзеров
        orm_all_results = await orm_get_all_results(session)
        ic(orm_all_results)
        cnt = len(orm_all_results) if orm_all_results else 1
        avg_result = sum(orm_all_results) / cnt

        # отправляем юзеру сообщение о завершении теста
        text = _("Тест завершен!\n\n"
                    "Ваш результат: {correct_count}/13\n\n"
                    "Ср.результат бота: {avg_result}/13\n"
                    "Ср.результат книги: 2.2/13").format(correct_count=correct_count, avg_result=avg_result)
        new_message = await callback_query.message.edit_text(text=text,
                                            reply_markup=get_callback_btns(btns={'Правильные ответы':'correct_answers',
                                                                                 'Больше о книге':'book_info',
                                                                                 'Статистика теста':'test_stats'},
                                                                        sizes=(1,1,1))) # type: ignore
        # Сохраняем новый message_id
        await state.update_data(last_message_id=new_message.message_id)
        await callback_query.answer()
