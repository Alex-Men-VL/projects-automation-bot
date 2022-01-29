from django.core.management import BaseCommand

from telegram_bot.models import Participant, ProductManager, Project, Team, Time

import logging
from turtle import title
from django import test


class Command(BaseCommand):
    def handle(self, *args, **options):
        # print teams with students WITHOUT creating in DB
        # sort_and_only_print_groups()

        # create teams with students in DB
        sort_and_create_teams()



def sort_and_create_teams():
    students = sort()  # sort() -> students = (junior, novice_plus, novice)
    for student_skill_group in students:
        groups = create_students_groups(student_skill_group)
        groups_with_call_time = []
        for group in groups:
            group = add_call_time_in_group(group)
            groups_with_call_time.append(group)

        prod_mngrs = ProductManager.objects.all()

        for group in groups_with_call_time:
            for prod_mngr in prod_mngrs:
                time = check_manager_free_time(prod_mngr, group[0])
                if time:
                    team = create_team(time, prod_mngr)
                    group.pop(0)
                    for student in group:
                        add_participant_in_team(team, student['id'])



def check_manager_free_time(manager, time: str):
    manager_free_times = Time.objects.filter(pm=manager).filter(
        team__isnull=True
    )
    for manager_time in manager_free_times:
        if manager_time.time_interval.strftime('%H%M') == time:
            return manager_time

    return False



def sort():
    participants = Participant.objects.select_related(
        'student', 'student__level'
    ).prefetch_related('times')
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

    students = sorted(
        students,
        key=lambda item: (item['level'], len(item['time']), item['time'])
    )

    return chunk_students_by_skill(students)


def chunk_students_by_skill(students):
    novice, novice_plus, junior = [], [], []

    for student in students:
        if student['level'] == 'junior':
            junior.append(student)

        if student['level'] == 'novice+':
            novice_plus.append(student)

        if student['level'] == 'novice':
            novice.append(student)

    return junior, novice_plus, novice



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
        resort_students = sorted(
            resort_students,
            key=lambda item: (len(item['time']), item['time'])
        )

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


def create_students_groups(students_sorted_by_skill):
    groups, resort_students = create_group_by_time(students_sorted_by_skill)

    while resort_students:
        another_groups, resort_students = create_group_by_time(resort_students)
        groups += another_groups

    return groups


def sort_and_only_print_groups():
    students = sort()  # sort() -> students = (novice, novice_plus, junior)
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
        groups = create_students_groups(student_skill_group)
        for group in groups:
            for student in group:
                print(student)
            print('----')
        print('====')


def create_team(call_time, prod_mngr):
    project = Project.objects.last()

    prod_mngr_name = prod_mngr.name
    call_time_for_title = call_time.time_interval.strftime('%H:%M')
    title = f'{prod_mngr_name}_{call_time_for_title}'

    team = Team(title=title, project=project, time=call_time)
    team.save()

    return team


def add_participant_in_team(team, student_id):
    participant = Participant.objects.get(student__pk=student_id)
    team.participants.add(participant)
