import logging
from django.core.management import BaseCommand
from telegram_bot.models import Participant, Student, ProductManager, StudentLevel, Time
from datetime import datetime

    
class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            students = sort()
            for student in students:
                print(student)
        except Exception as error:
            logging.error(error)


def sort():
    pts = Participant.objects.all()
    students = []

    for pt in pts:
        pt_times = pt.times.all()
        student_times = []
        for pt_time in pt_times:
            student_time = pt_time.time_interval.strftime('%H%M')
            student_times.append(
                student_time
            )
        student = {
            'name': pt.student.name,
            'id': pt.student.id,
            'level': pt.student.level.name,
            'time': student_times
        }
        students.append(student)
        print(student)

    return students
