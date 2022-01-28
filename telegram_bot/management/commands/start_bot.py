import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import Bot, BotCommand

from telegram_bot.tg_automation import (
    change_participant_time, handle_admin, TgBot,
    start,
    handle_poll,
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
            'CHANGE_TIME': change_participant_time,
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
            'teams': 'Get a list of generated teams',
        },
        'ru': {
            'help': 'Нужна помощь',
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
