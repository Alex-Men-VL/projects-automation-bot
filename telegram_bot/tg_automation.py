from telegram.ext import (
    CommandHandler,
    Updater
)

from telegram_bot.models import Student


def get_user(func):
    def wrapper(update, context):
        if update.message:
            tg_username = update.message.chat.username
        elif update.callback_query:
            tg_username = update.callback_query.message.chat.username  # FIXME: надо проверить, что в словаре такие ключи
        elif update.poll_answer:
            tg_username = update.poll_answer.user.username  # FIXME: надо проверить, что в словаре такие ключи
        else:
            return
        try:
            user = Student.objects.get(tg_username=tg_username)
        except Student.DoesNotExist:
            # TODO: надо сообщить пользователю, что он не ученик DVMN
            print('DoesNotExist')
            return
        context.user_data['user'] = user
        return func(update, context)

    return wrapper


class TgBot:

    def __init__(self, tg_token, states_functions):
        self.tg_token = tg_token
        self.states_functions = states_functions
        self.updater = Updater(token=tg_token, use_context=True)
        self.updater.dispatcher.add_handler(
            CommandHandler('start', get_user(self.handle_users_reply))
        )

    def handle_users_reply(self, update, context):
        user = context.user_data['user']
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
            self.update_user_data(chat_id, context)  # FIXME: может и не нужна
            user_state = user.bot_state  # FIXME: временное решение (возможно)
            user_state = user_state if user_state else 'NextState'  # FIXME: заменить на state, следующий после START

        state_handler = self.states_functions[user_state]
        next_state = state_handler(update, context)
        self.save_user_data(chat_id, context)  # FIXME: может и не нужна
        user.bot_state = next_state
        user.save()

    def update_user_data(self, chat_id, context):
        user_data = context.user_data
        user = user_data['user']
        # ...

    def save_user_data(self, chat_id, context):
        user_data = context.user_data
        user = user_data['user']
        # ...


def start(update, context):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id, 'Привет!', reply_markup=None)
    return 'NextState'
