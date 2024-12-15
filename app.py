# Режим запуска:
# docker == 1 - это запуск в docker - docker-compose up -d
# docker == 0 - это запуск локально - ctrl + B
docker = 0

import logging

# Настраиваем базовую конфигурацию логирования
logging.basicConfig(level=logging.INFO, format='  -  [%(asctime)s] #%(levelname)-5s -  %(name)s:%(lineno)d  -  %(message)s')
logger = logging.getLogger(__name__)

# Настраиваем логгер для SQLAlchemy
sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
sqlalchemy_logger.setLevel(logging.INFO)  # Устанавливаем нужный уровень (например, INFO)
sqlalchemy_logger.propagate = True  # Отключаем передачу сообщений основному логгеру, чтобы не задваивать их

import asyncio
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio.client import Redis
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import ConstI18nMiddleware, I18n, SimpleI18nMiddleware, FSMI18nMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from influxdb_client.client.write.point import Point
from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from config_data.config import Config, load_config

from handlers import other, admin, group, start, owner, donate, inline, factuality, correct_answer
from common.comands import private
from database.models import Base
from middlewares import counter, db, locale, throttle


# Загружаем конфиг в переменную config
config: Config = load_config()

# Инициализируем функцию для сбора аналитики, взаимодействуем с InfluxDB и Grafana
async def analytics(user_id: int, command_name: str, category_name: str):
    """Функция для сбора аналитики, взаимодействуем с InfluxDB и Grafana"""
    if docker == 1:
        try:
            # Настройка клиента для подключения к InfluxDB
            client = InfluxDBClient(url=config.influx.url, token=config.influx.token, org=config.influx.org)
            write_api = client.write_api(write_options=SYNCHRONOUS)
            current_time = datetime.now(timezone.utc)

            # Создаем Point для отправки в InfluxDB с временной меткой
            point = (
                    Point("bot_command_usage")
                    .tag("category", category_name)
                    .tag("command", command_name)
                    .tag("user_id", user_id)
                    .tag("ping", "ping")
                    .time(current_time)
                    .field("value", 1)
                    )

            # Записываем point в InfluxDB
            write_api.write(bucket=config.influx.bucket, org=config.influx.org, record=point)

        except Exception as e:
            logging.error("InfluxDB write error: %s", str(e))
        finally:
            client.close()
    else: # если docker == 0
        pass


# Инициализируем объект хранилища
if docker == 1:
    storage = RedisStorage(redis=Redis(host=config.redis.host, port=config.redis.port))  # данные хранятся на отдельном сервере Redis
else:
    storage = MemoryStorage()  # данные хранятся в оперативной памяти, при перезапуске всё стирается (для тестов и разработки)

logger.info('Инициализируем бот и диспетчер')
bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML,
                                       link_preview=None,
                                       link_preview_is_disabled=None,
                                       link_preview_prefer_large_media=None,
                                       link_preview_prefer_small_media=None,
                                       link_preview_show_above_text=None))
bot.owner = config.tg_bot.owner
bot.admin_list = config.tg_bot.admin_list
bot.home_group = config.tg_bot.home_group
bot.work_group = config.tg_bot.work_group


dp = Dispatcher(fsm_strategy=FSMStrategy.USER_IN_CHAT, storage=storage)
# USER_IN_CHAT  -  для каждого юзера, в каждом чате ведется своя запись состояний (по дефолту)
# GLOBAL_USER  -  для каждого юзера везде ведется своё состояние

# Создаем движок бд
if docker == 1:
    engine = create_async_engine(config.db.db_post, echo=False)  # PostgreSQL
else:
    engine = create_async_engine(config.db.db_lite, echo=False)  # SQLite (для тестов и разработки)

# Создаем ассинхроную сессию
session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Помещаем нужные объекты в workflow_data диспетчера
some_var_1 = 1
some_var_2 = 'Some text'
dp.workflow_data.update({'my_int_var': some_var_1,
                         'my_text_var': some_var_2,
                         'analytics': analytics})

# Подключаем мидлвари
dp.update.outer_middleware(throttle.ThrottleMiddleware())  # тротлинг чрезмерно частых действий пользователей
dp.update.outer_middleware(counter.CounterMiddleware())  # простой счетчик
dp.update.outer_middleware(db.DataBaseSession(session_pool=session_maker))  # мидлварь для прокидывания сессии БД
dp.update.outer_middleware(locale.LocaleFromDBMiddleware(workflow_data=dp.workflow_data))  # определяем локаль из БД и передам ее в FSMContext
i18n = I18n(path="locales", default_locale="ru", domain="bot_00_template")  # создаем объект I18n
dp.update.middleware(FSMI18nMiddleware(i18n=i18n))  # получяем язык на каждый апдейт, через обращение к FSMContext

# dp.update.middleware(ConstI18nMiddleware(locale='ru', i18n=i18n))  # задаем локаль как принудительно устанавливаемую константу
# dp.update.middleware(SimpleI18nMiddleware(i18n=i18n))  # задаем локаль по значению поля "language_code" апдейта

# Подключаем роутеры
dp.include_router(start.start_router)
dp.include_router(owner.owner_router)
dp.include_router(admin.admin_router)
dp.include_router(other.other_router)
dp.include_router(donate.donate_router)
dp.include_router(group.group_router)
dp.include_router(inline.inline_router)
dp.include_router(factuality.factuality_router)
dp.include_router(correct_answer.correct_answer_router)


# Типы апдейтов которые будем отлавливать ботом
# ALLOWED_UPDATES = ['message', 'edited_message', 'callback_query',]  # Отбираем определенные типы апдейтов
ALLOWED_UPDATES = dp.resolve_used_update_types()  # Отбираем только используемые события по роутерам

# Функция сработает при запуске бота
async def on_startup():
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    await bot.send_message(chat_id = bot.home_group[0], text = f"🤖  @{bot_username}  -  запущен!")

# Функция сработает при остановке работы бота
async def on_shutdown():
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    await bot.send_message(chat_id = bot.home_group[0], text = f"☠️  @{bot_username}  -  деактивирован!")

# Главная функция конфигурирования и запуска бота
async def main() -> None:

    # Удаление предыдущей версии базы, и создание новых таблиц заново
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    # Регистрируем функцию, которая будет вызвана автоматически при запуске/остановке бота
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Пропускаем накопившиеся апдейты - удаляем вебхуки (то что бот получил пока спал)
    await bot.delete_webhook(drop_pending_updates=True)

    # Удаляем ранее установленные команды для бота во всех личных чатах
    await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())

    # Добавляем свои команды
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())


    # Запускаем polling
    try:
        await dp.start_polling(bot,
                               allowed_updates=ALLOWED_UPDATES,)
                            #    skip_updates=False)  # Если бот будет обрабатывать платежи, НЕ пропускаем обновления!
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
