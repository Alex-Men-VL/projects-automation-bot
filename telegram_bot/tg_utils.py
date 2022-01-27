from datetime import date, datetime, timedelta

from . import static_text
from .models import Time


def get_time_intervals():
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
    message = context.bot.send_poll(
        chat_id=job_context['chat_id'],
        question=question,
        options=list(job_context['time_intervals'].keys()),
        is_anonymous=False,
        allows_multiple_answers=True,
    )


def add_participant_selected_times(participant, selected_intervals, intervals):
    time_ids = []
    for interval in selected_intervals:
        time_ids.extend(intervals[interval])
    times = Time.objects.filter(pk__in=time_ids)
    for time in times:
        participant.times.add(time)
