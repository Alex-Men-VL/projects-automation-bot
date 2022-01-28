import logging

from django.conf import settings
from django.core.management import BaseCommand
from telegram import Bot, BotCommand

from telegram_bot.tg_automation import (
    TgBot,
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
        }
    )
    bot.updater.start_polling()
    bot.updater.idle()


bot_instance = Bot(settings.TELEGRAM_BOT_TOKEN)


def set_up_commands(bot_instance):
    langs_with_commands = {
        'en': {
            'change_time': 'Choose the time again',
            # 'admin': 'Get administrator rights',
        },
        'ru': {
            'change_time': 'Выбрать время заново',
            # 'admin': 'Получить права администратора',

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
