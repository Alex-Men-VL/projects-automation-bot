from datetime import time  # Не удалять

from django.db import transaction
from telegram.ext import (
    CommandHandler,
    PollAnswerHandler,
    Updater
)

from . import static_text
from .models import Participant, ProductManager, Project, Student
from .tg_utils import (
    add_participant_in_team, add_participant_selected_times,
    get_time_intervals,
    send_notification, send_poll_with_times
)


def get_user(func):
    def wrapper(update, context):
        if update.message:
            tg_username = update.message.chat.username
        elif update.callback_query:
            tg_username = update.callback_query.message.chat.username
        elif update.poll_answer:
            tg_username = update.poll_answer.user.username
        else:
            return
        try:
            student = Student.objects.get(tg_username=tg_username)
            context.user_data['student'] = student
        except Student.DoesNotExist:
            try:
                pm = ProductManager.objects.get(tg_username=tg_username)
                context.user_data['pm'] = pm
            except ProductManager.DoesNotExist:
                # TODO: надо сообщить пользователю, что он не ученик DVMN
                return
        return func(update, context)

    return wrapper


class TgBot:

    def __init__(self, tg_token, states_functions):
        self.tg_token = tg_token
        self.states_functions = states_functions
        self.updater = Updater(token=tg_token, use_context=True)
        self.updater.dispatcher.add_handler(
            PollAnswerHandler(get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_handler(
            CommandHandler('start', get_user(self.handle_users_reply))
        )

    def handle_users_reply(self, update, context):
        user = context.user_data.get('student') or context.user_data.get('pm')
        if update.message:
            chat_id = update.message.chat_id
            user_reply = update.message.text
        elif update.callback_query:
            chat_id = update.callback_query.message.chat_id
            user_reply = update.callback_query.data
        elif update.poll_answer:
            chat_id = update.poll_answer.user.id
            user_reply = update.poll_answer.option_ids
        else:
            return
        if user_reply == '/start':
            user_state = 'START'
        else:
            user_state = user.bot_state
            user_state = user_state if user_state else 'HANDLE_POLL'

        self.update_user_data(context, chat_id, user)
        if 'time_intervals' not in context.bot_data:
            self.update_bot_data(context)

        state_handler = self.states_functions[user_state]
        next_state = state_handler(update, context)
        user.bot_state = next_state
        user.save()

    def update_user_data(self, context, chat_id, user):
        user_data = context.user_data
        user_data['chat_id'] = chat_id
        user_data['username'] = user.tg_username

    def update_bot_data(self, context):
        bot_data = context.bot_data
        bot_data['time_intervals'] = get_time_intervals()


def start(update, context):
    chat_id = update.message.chat_id
    if student := context.user_data.get('student'):
        message = static_text.start_message
        context.bot.send_message(chat_id, message, reply_markup=None)
        if context.user_data.get('student'):
            '''Раскомментировать на продакшене
            context.job_queue.run_monthly(
                send_poll_with_times,
                time(17, 0, 0),
                day=13,
                context={'chat_id': chat_id,
                         'time_intervals': context.bot_data['time_intervals']},
                name=context.user_data['username'])
            context.job_queue.run_monthly(
                send_notification,
                time(17, 0, 0),
                day=17,
                context={'chat_id': chat_id, 'student': student},
                name=f'{context.user_data["username"]} notification'
            )'''

            # Закомментировать на продакшене
            context.job_queue.run_once(
                send_poll_with_times,
                when=2,
                context={'chat_id': chat_id,
                         'time_intervals': context.bot_data['time_intervals']},
                name=context.user_data['username'],
            )
            context.job_queue.run_once(
                send_notification,
                when=5,
                context={'chat_id': chat_id, 'student': student},
                name=f'{context.user_data["username"]} notification'
            )
        return 'HANDLE_POLL'


@transaction.atomic
def handle_poll_answer(update, context):
    student = context.user_data['student']
    chat_id = context.user_data['chat_id']
    project = Project.objects.last()
    participant, created = Participant.objects.get_or_create(
        student=student,
        project=project
    )
    poll_options = context.bot_data['time_intervals']
    answers = [time_interval for time_id, time_interval in
               enumerate(poll_options) if time_id in
               update.poll_answer.option_ids]
    if created:
        add_participant_selected_times(participant, answers, poll_options)
    elif answers:
        team = add_participant_in_team(participant, answers[0],
                                       poll_options)

        if team:
            team_time = team.time.time_interval.strftime('%H:%M')
            message = static_text.success_message.format(time=team_time)
            context.bot.send_message(
                chat_id,
                message,
                reply_markup=None
            )
        else:
            message = static_text.unsuccessful_message
            context.bot.send_message(
                chat_id,
                message
            )
            context.job_queue.run_once(
                send_notification,
                when=1,
                context={'chat_id': chat_id, 'student': student},
                name=f'{context.user_data["username"]} notification'
            )
    return 'HANDLE_POLL'
