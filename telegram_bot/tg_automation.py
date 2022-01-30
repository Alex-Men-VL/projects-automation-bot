import html
import json
import logging
import traceback

from django.conf import settings
from django.db import transaction
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ParseMode,
    ReplyKeyboardRemove,
    Update
)
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    PollAnswerHandler,
    Updater
)

from . import static_text
from .models import Participant, ProductManager, Project, Student
from .tg_utils import (
    add_participant_in_team, add_participant_selected_times,
    get_time_intervals,
    install_collect_teams_job, install_first_week_job, install_second_week_job,
    send_list_of_commands,
    send_notification,
    send_poll_with_times
)

logger = logging.getLogger('tg_bot')


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
            context.user_data['not_found'] = False
        except Student.DoesNotExist:
            try:
                pm = ProductManager.objects.get(tg_username=tg_username)
                context.user_data['pm'] = pm
                context.user_data['not_found'] = False
            except ProductManager.DoesNotExist:
                context.user_data['not_found'] = True
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
            MessageHandler(Filters.text & ~Filters.command & Filters.regex(
                r'[0-9]{2}:[0, 3]0-[0-9]{2}:[0, 3]0'
            ), get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_handler(
            MessageHandler(Filters.text & ~Filters.command,
                           self.handle_unregistered_message)
        )
        self.updater.dispatcher.add_handler(
            CommandHandler('start', get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_handler(
            CommandHandler('change_time', get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_handler(
            CommandHandler('leave_project', get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_handler(
            CommandHandler('help', self.help_handler)
        )
        self.updater.dispatcher.add_handler(
            CommandHandler('teams', get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_handler(
            CallbackQueryHandler(get_user(self.handle_users_reply))
        )
        self.updater.dispatcher.add_error_handler(self.error_handler)

    def handle_users_reply(self, update, context):
        if context.user_data['not_found']:
            return handle_person_not_found(update, context)
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
        elif user_reply == '/change_time':
            user_state = 'CHANGE_TIME'
        elif user_reply == '/leave_project':
            user_state = 'LEAVE_PROJECT'
        elif user_reply == '/teams':
            if not context.user_data.get('pm', False):
                send_permission_denied(update)
                return
            else:
                user_state = 'ADMIN'
        else:
            user_state = user.bot_state
            user_state = user_state if user_state else 'HANDLE_POLL'

        self.update_user_data(context, chat_id, user)
        if 'time_intervals' not in context.bot_data:
            self.update_bot_data(context)

        state_handler = self.states_functions[user_state]
        next_state = state_handler(update, context)
        user.chat_id = chat_id
        user.bot_state = next_state
        user.save()

    def update_user_data(self, context, chat_id, user):
        user_data = context.user_data
        user_data['chat_id'] = chat_id
        user_data['username'] = user.tg_username

    def update_bot_data(self, context):
        bot_data = context.bot_data
        bot_data['time_intervals'] = get_time_intervals()

    def help_handler(self, update, context):
        update.message.reply_text(static_text.help_message)

    def handle_unregistered_message(self, update, context):
        update.message.reply_text(static_text.unregistered_message)

    def error_handler(self, update, context):
        logger.error(msg="Произошла ошибка: ", exc_info=context.error)

        if update.effective_message:
            text = static_text.error_text
            update.effective_message.reply_text(text)

        tb_list = traceback.format_exception(None, context.error,
                                             context.error.__traceback__)
        tb_string = ''.join(tb_list)
        update_str = update.to_dict() if isinstance(update, Update) else \
            str(update)
        message = static_text.error_dev_text.format(
            update=html.escape(json.dumps(
                update_str,
                indent=2,
                ensure_ascii=False
            )),
            chat_data=html.escape(str(context.chat_data)),
            user_data=html.escape(str(context.user_data)),
            tb_string=html.escape(tb_string)
        )
        devs = settings.DEVS_CHAT_ID
        for dev_id in devs:
            context.bot.send_message(dev_id, message, parse_mode=ParseMode.HTML)


def start(update, context):
    install_second_week_job(context)
    install_collect_teams_job(context)

    chat_id = update.message.chat_id
    if student := context.user_data.get('student'):
        message = static_text.start_message.format(
            name=student.name.split()[0]
        )
        context.bot.send_message(chat_id, message,
                                 reply_markup=ReplyKeyboardRemove())
        install_first_week_job(context, student, chat_id)
        return 'HANDLE_POLL'
    elif pm := context.user_data.get('pm'):
        message = static_text.admin_message.format(
            name=pm.name.split()[0]
        )
        context.bot.send_message(
            context.user_data['chat_id'],
            message
        )
        return 'ADMIN'


@transaction.atomic
def handle_poll(update, context):
    student = context.user_data['student']
    project = Project.objects.last()
    participant, created = Participant.objects.get_or_create(
        student=student,
        project=project
    )
    if update.poll_answer and update.poll_answer.option_ids:
        return handle_poll_answer(update, context, participant, created)

    if update.poll_answer and not update.poll_answer.option_ids:
        message = static_text.warning_message
        context.bot.send_message(
            context.user_data['chat_id'],
            message,
            reply_markup=ReplyKeyboardRemove()
        )
        return 'HANDLE_POLL'
    if update.message and (answer := update.message.text):
        return handle_poll_message(context, participant, answer)


def handle_poll_answer(update, context, participant, created):
    chat_id = context.user_data['chat_id']
    poll_options = context.bot_data['time_intervals']
    answers = [time_interval for time_id, time_interval in
               enumerate(poll_options) if time_id in
               update.poll_answer.option_ids]
    if created:
        add_participant_selected_times(participant, answers, poll_options)
    elif answers:
        send_poll_report(context, participant, answers, poll_options, chat_id)
    return 'HANDLE_POLL'


def handle_poll_message(context, participant, answer):
    chat_id = context.user_data['chat_id']
    poll_options = context.bot_data['time_intervals']
    send_poll_report(context, participant, [answer], poll_options, chat_id)
    return 'HANDLE_POLL'


def send_poll_report(context, participant, answers, poll_options, chat_id):
    team = add_participant_in_team(participant, answers[0], poll_options)

    if team:
        team_time = team.time.time_interval.strftime('%H:%M')
        message = static_text.success_message.format(time=team_time)
        context.bot.send_message(
            chat_id,
            message,
            reply_markup=ReplyKeyboardRemove()
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
            context={'chat_id': chat_id, 'student': participant.student},
            name=f'{context.user_data["username"]} notification'
        )


def handle_change_participation(update, context, delete_pt=False):
    if student := context.user_data.get('student'):
        participant = Participant.objects.filter(
            project=Project.objects.last()
        ).filter(student=student)
        if participant.exists():
            participant = participant[0]
            if not participant.team:
                participant.delete()
                if not delete_pt:
                    message = static_text.change_time_message
                    context.job_queue.run_once(
                        send_poll_with_times,
                        when=3,
                        context={
                            'chat_id': student.chat_id,
                            'time_intervals': context.bot_data['time_intervals']
                        },
                        name=context.user_data['username'])
                else:
                    message = static_text.leave_project_success_message
            else:
                message = static_text.change_participation_message
        else:
            message = static_text.unsuccessful_change_participation_message

        if message:
            context.bot.send_message(
                student.chat_id,
                message
            )
        return 'HANDLE_POLL'


def handle_leave_project(update, context):
    if update.callback_query:
        if update.callback_query.data == 'Покинуть':
            handle_change_participation(update, context, delete_pt=True)

        message_id = context.user_data.pop('delete_message_id')
        context.bot.delete_message(context.user_data['chat_id'], message_id)
        return 'HANDLE_POLL'
    else:
        button = [
            [InlineKeyboardButton('Да', callback_data='Покинуть'),
             InlineKeyboardButton('Нет', callback_data='Не покидать')]
        ]
        message = context.bot.send_message(
            context.user_data['chat_id'],
            static_text.leave_project_confirmation,
            reply_markup=InlineKeyboardMarkup(button)
        )
        context.user_data['delete_message_id'] = message.message_id
    return 'LEAVE_PROJECT'


def send_permission_denied(update):
    update.message.reply_text(static_text.permission_denied_message)


def handle_admin(update, context):
    pm = context.user_data['pm']
    send_list_of_commands(context, pm)
    return 'ADMIN'


def handle_person_not_found(update, context):
    message = static_text.unregistered_user_message.format(
        site_url=settings.DVMN_URL
    )
    update.message.reply_text(message)
