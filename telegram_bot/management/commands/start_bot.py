import logging

from django.conf import settings
from django.core.management import BaseCommand

from telegram_bot.tg_automation import (
    handle_poll_answer, TgBot,
    start,
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
            'FIRST_INTERVAL': handle_poll_answer,
        }
    )
    bot.updater.start_polling()
    bot.updater.idle()
