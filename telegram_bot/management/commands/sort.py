import logging
from django.core.management import BaseCommand
from telegram_bot.models import Participant, Team


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            # create teams with students in DB
            # sort_and_create_teams()

            # print teams with students WITHOUT creating in DB
            sort_and_only_print_groups()

        except Exception as error:
            logging.error(error)


# data example for student:
# {'name': 'Student_1', 'id': 1, 'level': 'beginner', 'time': ['1900']}

# main func
def sort_and_create_teams():
    students = sort() # sort() -> students = (novice, novice_plus, junior)
    for student_skill_group in students:
        groups = create_studets_groups(student_skill_group)
        for group in groups:
            team = create_team(group[0]['id'])
            for student in group:
                add_participant_in_team(team, student['id'])


def sort():
    participants = Participant.objects.all()
    students = []

    for pt in participants:
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

    students = sorted(students, key=lambda item: (item['level'], len( item['time']), item['time']))

    return chunk_students_by_skill(students)


def chunk_students_by_skill(students):
    novice, novice_plus, junior = [], [], []

    for student in students:
        if student['level'] == 'novice':
            novice.append(student)

        if student['level'] == 'novice+':
            novice_plus.append(student)

        if student['level'] == 'junior':
            junior.append(student)

    return (novice, novice_plus, junior)


def create_group_by_time(students_group):
    print('START CREATING')
    students_group = sorted(students_group, key=lambda item: (item['time']))
    resort_students = []
    groups = []
    group = []
    time = None
    for student in students_group:
        if len(group) == 0:
            group.append(student)
            time = student['time'][0]

        elif len(group) == 1 and time in student['time']:
            group.append(student)

        elif len(group) == 1 and time not in student['time']:
            resort_students.append(group[0])
            group = []
            group.append(student)
            time = student['time'][0]

        elif len(group) == 2 and time in student['time']:
            group.append(student)
            groups.append(group)  
            group = []
            time = None

        elif len(group) == 2 and time not in student['time']:
            resort_students.append(student)
            groups.append(group)
            group = []
            time = None

    if len(group) == 1:
        resort_students.append(group[0])

    if len(group) == 2:
        groups.append(group)
    
    if len(resort_students) != 0:
        resort_students = sorted(resort_students, key=lambda item: (len( item['time']), item['time']))

    return groups, resort_students


def check_the_same_time_slots(resort_students):
    time_slots = []
    for student in resort_students:
        time_slots += student['time']

    test_time_slots = []

    for time_slot in time_slots:
        if time_slot in test_time_slots:
            return True

        else:
            test_time_slots.append(time_slot)

    return False


def create_studets_groups(students_sorted_by_skill):
    groups, resort_students = create_group_by_time(students_sorted_by_skill)
    
    if check_the_same_time_slots(resort_students):
        print('RESORT STUDENTS ', resort_students)
        more_groups, more_resort_students = create_group_by_time(resort_students)
        print('MORE GROUP ', more_groups)
        groups += more_groups
    else:
        print('HAS NO The SAAAAAme')

    return groups


def create_team(student_id, team_title='default_name'):
    participant = Participant.objects.get(student__pk=student_id)
    team = Team(title=team_title, project=participant.project, time=participant.times.all()[0])
    team.save()

    return team


def add_participant_in_team(team, student_id):
    participant = Participant.objects.get(student__pk=student_id)
    team.participants.add(participant)


def sort_and_only_print_groups():
    students = sort() # sort() -> students = (novice, novice_plus, junior)
    print()
    print('=== sorted students ===')
    for skill_groups in students:
        for student in skill_groups:
            print(student)
        print('-----------')
    print('=== sorted students ===')
    print()
    print('=== students_by_groups ===')
    for student_skill_group in students:
        groups = create_studets_groups(student_skill_group)
        for group in groups:
            for student in group:
                print(student)
            print('----')
        print('====')