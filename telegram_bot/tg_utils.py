from datetime import date, datetime, timedelta

from django.db.models import Count
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from . import static_text
from .models import Participant, Team, Time


def get_time_intervals(special_times=None):
    if special_times:
        interval_start_times = special_times
    else:
        interval_start_times = Time.objects.order_by(
            'time_interval'
        ).values_list('time_interval', 'id')

    diff_interval_start_times = {}
    for start_time, time_id in interval_start_times:
        diff_interval_start_times.setdefault(start_time, []).append(time_id)
    time_intervals = {}
    delta = timedelta(minutes=30)
    for start_time, time_ids in diff_interval_start_times.items():
        end_time = (datetime.combine(date(1, 1, 1), start_time) + delta).time()

        formatted_start_time = start_time.strftime('%H:%M')
        formatted_end_time = end_time.strftime('%H:%M')
        time_intervals.update({
            f'{formatted_start_time}-{formatted_end_time}': time_ids
        })
    return time_intervals


def send_poll_with_times(context):
    question = static_text.poll_question
    job_context = context.job.context
    if (special_times := job_context.get('special_times', False)) or \
            special_times == {}:
        options = special_times
        allows_multiple_answers = False
    else:
        options = job_context['time_intervals']
        allows_multiple_answers = True
    if len(options) > 1:
        message = context.bot.send_poll(
            chat_id=job_context['chat_id'],
            question=question,
            options=list(options.keys()),
            is_anonymous=False,
            allows_multiple_answers=allows_multiple_answers,
        )
    elif len(options) == 1:
        message = static_text.poll_question_with_one_option
        button = [
            [
                KeyboardButton(list(options.keys())[0])
            ]
        ]
        context.bot.send_message(
            job_context['chat_id'],
            message,
            reply_markup=ReplyKeyboardMarkup(button,
                                             one_time_keyboard=True,
                                             resize_keyboard=True)
        )
    else:
        message = static_text.poll_question_with_zero_option
        context.bot.send_message(
            job_context['chat_id'],
            message,
            reply_markup=ReplyKeyboardRemove()
        )


def send_notification(context):
    job_context = context.job.context
    student = job_context['student']
    participant = Participant.objects.get(student=student)
    if participant.team:
        team_time = participant.team.time.time_interval.strftime('%H:%M')
        context.bot.send_message(
            job_context['chat_id'],
            static_text.success_message.format(time=team_time),
            reply_markup=None
        )
    else:
        available_times = get_available_times(student)
        if not available_times:
            time_intervals = {}
        else:
            time_intervals = get_time_intervals(special_times=available_times)

        context.job_queue.run_once(
            send_poll_with_times,
            when=1,
            context={'chat_id': job_context['chat_id'],
                     'special_times': time_intervals},
        )


def get_available_times(student):
    available_teams = Team.objects.annotate(
        participants_count=Count('participants')
    ).filter(participants_count__exact=2).prefetch_related(
        'participants'
    ).select_related('time')
    available_teams_for_student = []
    for team in available_teams:
        participants = team.participants.select_related('student__level')
        team_level = set(pt.student.level for pt in participants)
        if student.level in team_level:
            available_teams_for_student.append(team)
    available_times = [(team.time.time_interval, team.pk) for team in
                       available_teams_for_student]
    return available_times


def add_participant_selected_times(participant, selected_intervals, intervals):
    time_ids = []
    for interval in selected_intervals:
        time_ids.extend(intervals[interval])
    times = Time.objects.filter(pk__in=time_ids)
    for time in times:
        participant.times.add(time)


def add_participant_in_team(participant, selected_interval, intervals):
    time_ids = intervals[selected_interval]
    team = Team.objects.filter(time__in=time_ids).annotate(
        participant_count=Count('participants')
    ).filter(participant_count__exact=2).first()
    if team:
        team.participants.add(participant)
    return team
