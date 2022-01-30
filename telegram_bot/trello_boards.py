import logging

import requests
from django.conf import settings

from telegram_bot.models import Project, Team


def create_workspace(project_name, project_start_date, project_end_date,
                     trello_key, trello_token):
    project = f'Проект {project_name} [{project_start_date}-{project_end_date}]'
    url = 'https://api.trello.com/1/organizations/'
    query = {
        'key': trello_key,
        'token': trello_token,
        'displayName': project
    }
    headers = {'Accept': 'application/json'}
    response = requests.post(url, params=query, headers=headers)
    response.raise_for_status()
    workspace = response.json()
    return workspace['id']


def create_board(board_name, workspace, prefs_background,
                 trello_key, trello_token):
    url = 'https://api.trello.com/1/boards/'
    query = {
        'name': board_name,
        'key': trello_key,
        'token': trello_token,
        'idOrganization': workspace,
        'prefs_background': prefs_background
    }
    response = requests.request('POST', url, params=query)
    response.raise_for_status()
    board_url = response.json()['shortUrl']
    return board_url


def create_project_boards(pm=None):
    logger = logging.getLogger('tg_bot')

    trello_key = settings.TRELLO_KEY
    trello_token = settings.TRELLO_TOKEN

    project = Project.objects.last()
    if not project.workspace_id:
        project_name = project.title
        project_start = project.start.strftime('%d.%m')
        project_end = project.end.strftime('%d.%m')

        try:
            workspace = create_workspace(project_name, project_start,
                                         project_end, trello_key, trello_token)
        except requests.exceptions.RequestException:
            logger.error(
                f'Рабочее пространство для проекта "{project_name}" не создано.'
            )
        project.workspace_id = workspace
        project.save()

    teams = Team.objects.filter(project=project)
    if pm:
        teams = teams.filter(time__pm=pm)

    teams = teams.select_related('time').prefetch_related(
        'participants', 'participants__student'
    )

    backgrounds = ['blue', 'orange', 'green', 'red', 'purple', 'pink',
                   'lime', 'sky', 'grey']
    for team in teams:
        if not team.trello_link:
            pm_id = team.time.pm_id
            background = backgrounds[pm_id]
            time = str(team.time).split(' ')[1]
            participants = team.participants.all()
            names = ''
            for participant in participants:
                name = participant.student.name.split(' ')[0]
                names = names + ', ' + name
            board_name = time + names
            try:
                trello_link = create_board(board_name, workspace, background,
                                           trello_key, trello_token)
            except requests.exceptions.RequestException:
                logger.error(
                    f'Доска {board_name} не создана.'
                )
            team.trello_link = trello_link
            team.save()
    logger.info(
        f'Рабочее пространство и комнаты для проекта "{project.title}" созданы'
    )
