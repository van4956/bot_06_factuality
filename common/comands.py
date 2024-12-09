# список команд которые мы отправляем боту
# команды в кнопке "Меню", либо через знак "/"

from aiogram.types import BotCommand

private = [
    BotCommand(command='information',description='information about the bot'),
    BotCommand(command='factuality',description='start factuality test'),
    BotCommand(command='language',description='change language'),
    BotCommand(command='terms',description='terms of use'),
]
