import logging
# from os import getgrouplist
from django.core.management import BaseCommand
from telegram_bot.models import Participant, Student, ProductManager, StudentLevel, Time
# from datetime import datetime

    
class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            students = sort()
            # for student in students:
            #     print(student)
            groups = create_studets_groups(students)
            for group in groups:
                for student in group:
                    print(student)
                print('----')

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

    students = sorted(students, key=lambda item: (item['level'], item['time']))

    return students


def create_studets_groups(students):
    single_users = []
    group = []
    groups = []
    time = None

    for student in students:
        if len(group) == 0:
            group.append(student)
            time = student['time'][0]

        elif len(group) == 1 and time in student['time']:
            group.append(student)

        elif len(group) == 1 and time not in student['time']:
            single_users.append(student)
            group = []
            time = None

        elif len(group) == 2 and time in student['time']:
            group.append(student)
            groups.append(group)  
            group = []
            time = None

        elif len(group) == 2 and time not in student['time']:
            group.append(student)
            groups.append(group)
            group = []
            time = None
        else:
            pass

    return groups


# {'name': 'Student_1', 'id': 1, 'level': 'beginner', 'time': ['1900']}
# {'name': 'Student_3', 'id': 3, 'level': 'beginner', 'time': ['1900']}
# {'name': 'Student_5', 'id': 5, 'level': 'beginner', 'time': ['1900']}
# {'name': 'Student_7', 'id': 7, 'level': 'beginner', 'time': ['1930']}
# {'name': 'Student_8', 'id': 8, 'level': 'beginner', 'time': ['1930']}
# {'name': 'Student_9', 'id': 9, 'level': 'beginner', 'time': ['1930']}
# {'name': 'Student_6', 'id': 6, 'level': 'junior', 'time': ['1830']}
# {'name': 'Student_2', 'id': 2, 'level': 'junior', 'time': ['1830', '1900']}
# {'name': 'Student_4', 'id': 4, 'level': 'junior', 'time': ['1830', '1900', '1930']}