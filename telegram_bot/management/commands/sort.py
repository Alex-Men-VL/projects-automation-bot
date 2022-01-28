import logging
from django import test
from django.core.management import BaseCommand
from telegram_bot.models import Participant, Team


class Command(BaseCommand):
    def handle(self, *args, **options):
        # print teams with students WITHOUT creating in DB
        sort_and_only_print_groups()

        # create teams with students in DB
        sort_and_create_teams()

        


def sort_and_create_teams():
    students = sort() # sort() -> students = (novice, novice_plus, junior)
    for student_skill_group in students:
        groups = create_studets_groups(student_skill_group)

        for group in groups:
            group = add_call_time_in_group(group)
            team = create_team(group[1]['id'], group[0])
            group.pop(0)

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


def add_call_time_in_group(group):
    first_member_call_times = set(group[0]['time'])
  
    for member in group:
        common_times = set(member['time']) & first_member_call_times

    for common_time in common_times:
        break

    group.insert(0, common_time)

    return group


def create_group_by_time(students_group):
    students_group = sorted(students_group, key=lambda item: (item['time']))

    resort_students = []
    groups = []
    group = []

    for student in students_group:
        if not group:
            group.append(student)
            time = student['time']
        
        elif len(group) == 2 and check_the_same_element(time, student['time']):
            group.append(student)
            groups.append(group)  
            group = []
            time = None

        elif len(group) < 3 and check_the_same_element(time, student['time']):
            group.append(student)

        else:
            resort_students.append(student)

    if len(group) == 1:
        students_group.remove(group[0])

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


def check_the_same_element(list_1, list_2):
    for element in list_2:
        if element in list_1:

            return True

    return False


def create_studets_groups(students_sorted_by_skill):
    groups, resort_students = create_group_by_time(students_sorted_by_skill)

    while resort_students:
        another_groups, resort_students = create_group_by_time(resort_students)
        groups += another_groups

    return groups


def create_team(student_id, call_time, team_title='default_name'):
    participant = Participant.objects.get(student__pk=student_id)

    for participant_time in participant.times.all():
        if participant_time.time_interval.strftime('%H%M') == call_time:
            print('TIME: ', participant_time)
            print('TIME: ', participant_time.time_interval.strftime('%H%M'))
            break

    team = Team(title=team_title, project=participant.project, time=participant_time)
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