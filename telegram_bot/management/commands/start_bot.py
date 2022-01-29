import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import Bot, BotCommand

from telegram_bot.tg_automation import (
    handle_admin,
    handle_change_participation,
    handle_leave_project,
    handle_poll,
    start,
    TgBot
)


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            start_bot()
        except Exception as error:
            logging.error(error)


def start_bot():
    tg_token = settings.TELEGRAM_BOT_TOKEN
    bot = TgBot(
        tg_token,
        {
            'START': start,
            'HANDLE_POLL': handle_poll,
            'CHANGE_TIME': handle_change_participation,
            'LEAVE_PROJECT': handle_leave_project,
            'ADMIN': handle_admin,
        }
    )
    bot.updater.start_polling()
    bot.updater.idle()


bot_instance = Bot(settings.TELEGRAM_BOT_TOKEN)


def set_up_commands(bot_instance):
    langs_with_commands = {
        'en': {
            'help': 'Need help',
            'change_time': 'Change the selected call time',
            'leave_project': 'Leave the project',
            'teams': 'Get a list of generated teams',
        },
        'ru': {
            'help': 'Нужна помощь',
            'change_time': 'Изменить выбранное время созвона',
            'leave_project': 'Покинуть проект',
            'teams': 'Получить список сформированных команд',
        }
    }

    bot_instance.delete_my_commands()
    for language_code in langs_with_commands:
        bot_instance.set_my_commands(
            language_code=language_code,
            commands=[
                BotCommand(command, description) for command, description in
                langs_with_commands[language_code].items()
            ]
        )


set_up_commands(bot_instance)
