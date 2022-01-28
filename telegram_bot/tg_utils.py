from datetime import date, datetime, time, timedelta

from django.db.models import Count
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

from . import static_text
from .models import Participant, ProductManager, Project, Student, Team, Time


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
        if len(options) == 1:
            message = static_text.poll_question_with_one_option
        elif len(options) == 0:
            message = static_text.poll_question_with_zero_option
        else:
            message = static_text.poll_question
        buttons = []
        for time_interval in options.keys():
            buttons.append([time_interval])

        if buttons:
            reply_markup = ReplyKeyboardMarkup(buttons,
                                               one_time_keyboard=True,
                                               resize_keyboard=True)
        else:
            reply_markup = ReplyKeyboardRemove()

        context.bot.send_message(
            job_context['chat_id'],
            message,
            reply_markup=reply_markup
        )
    else:
        options = job_context['time_intervals']
        context.bot.send_poll(
            chat_id=job_context['chat_id'],
            question=question,
            options=list(options.keys()),
            is_anonymous=False,
            allows_multiple_answers=True,
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
    for selected_time in times:
        participant.times.add(selected_time)


def add_participant_in_team(participant, selected_interval, intervals):
    time_ids = intervals[selected_interval]
    team = Team.objects.filter(time__in=time_ids).annotate(
        participant_count=Count('participants')
    ).filter(participant_count__exact=2).first()
    if team:
        team.participants.add(participant)
    return team


def install_first_week_job(context, student, chat_id):
    # Раскомментировать на продакшене
    # start_first_week_job(context, chat_id, student)

    # Закомментировать на продакшене
    if not Participant.objects.filter(
            project=Project.objects.last()
    ).filter(student=student).exists():
        context.job_queue.run_once(
            send_poll_with_times,
            when=2,
            context={'chat_id': chat_id,
                     'time_intervals': context.bot_data['time_intervals']},
            name=context.user_data['username'],
        )
    context.job_queue.run_once(
        send_notification,
        when=10,
        context={'chat_id': chat_id, 'student': student},
        name=f'{context.user_data["username"]} notification'
    )


def start_first_week_job(context, student):
    first_job = context.job_queue.get_jobs_by_name(
        context.user_data['username']
    )
    if not first_job:
        context.job_queue.run_monthly(
            send_poll_with_times,
            time(17, 0, 0),
            day=13,
            context={'chat_id': student.chat_id,
                     'time_intervals': context.bot_data['time_intervals']},
            name=context.user_data['username'])
    second_job = context.job_queue.get_jobs_by_name(
        f'{context.user_data["username"]} notification'
    )
    if not second_job:
        context.job_queue.run_monthly(
            send_notification,
            time(17, 0, 0),
            day=17,
            context={'chat_id': student.chat_id, 'student': student},
            name=f'{context.user_data["username"]} notification'
        )


def install_second_week_job(context):
    second_week_job = context.job_queue.get_jobs_by_name('next_week')
    if not second_week_job:
        context.job_queue.run_monthly(
            start_second_week_job,
            time(17, 0, 0),
            day=20,
            name='next_week'
        )


def start_second_week_job(context):
    students_taking_part = Participant.objects.filter(
        project=Project.objects.last()
    ).values_list('student__id', flat=True)
    remaining_students = Student.objects.exclude(id__in=students_taking_part)
    for student in remaining_students:
        context.job_queue.run_once(
            send_poll_with_times,
            when=1,
            context={'chat_id': student.chat_id,
                     'time_intervals': context.bot_data['time_intervals']},
            name=context.user_data['username'])

        context.job_queue.run_monthly(
            send_notification,
            time(17, 0, 0),
            day=21,
            context={'chat_id': student.chat_id, 'student': student},
            name=f'{context.user_data["username"]} notification'
        )


def send_list_of_commands(context, pm):
    # current_pm_teams = Team.objects.filter(time__pm=pm).
    pm = ProductManager.objects.get(name='Катя')
    current_pm_teams = Team.objects.filter(
        time__pm=pm
    ).annotate(
        participants_count=Count('participants')
    ).filter(participants_count__exact=3).prefetch_related(
        'participants__student'
    ).select_related('time')
    for number, team in enumerate(current_pm_teams, start=1):
        participants = team.participants.values_list('student__name',
                                                     'student__tg_username')
        message = static_text.team_info.format(
            number=number,
            first_pt=participants[0][0],
            first_tg=participants[0][1],
            second_pt=participants[1][0],
            second_tg=participants[1][1],
            third_pm=participants[2][0],
            third_tg=participants[2][1],
            team_time=team.time.time_interval.strftime('%H:%M')
        )
        context.bot.send_message(
            context.user_data['chat_id'],
            message
        )
    if not current_pm_teams:
        context.bot.send_message(
            context.user_data['chat_id'],
            static_text.admin_there_are_no_commands
        )
