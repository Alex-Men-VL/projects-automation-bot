import logging

from django.core.management import BaseCommand

from telegram_bot.trello_boards import create_project_boards


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            create_project_boards()
        except Exception as error:
            logging.error(error)
