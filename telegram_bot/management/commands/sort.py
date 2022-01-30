from django.core.management import BaseCommand

from telegram_bot.collect_teams import (
    sort_and_create_teams,
    sort_and_only_print_groups
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        # print teams with students WITHOUT creating in DB
        # sort_and_only_print_groups()

        # create teams with students in DB
        sort_and_create_teams()
