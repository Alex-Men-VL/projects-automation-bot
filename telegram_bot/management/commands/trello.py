import logging
from django.core.management import BaseCommand
from telegram_bot.models import Team, Project
import requests
import trello
from environs import Env

    
class Command(BaseCommand):
      def handle(self, *args, **options):
        try:
            trello()
        except Exception as error:
            logging.error(error)


env = Env()
env.read_env()
trello_key = env.str('TRELLO_KEY')
trello_token = env.str('TRELLO_TOKEN')


def create_workspace(project_name, project_start_date, project_end_date):
    project = f'Проект {project_name} [{project_start_date}-{project_end_date}]'
    url = 'https://api.trello.com/1/organizations/'
    query = {
        'key': trello_key,
        'token': trello_token,
        'displayName': project
    }
    headers = {'Accept': 'application/json'}
    respone = requests.post(url, params=query, headers=headers)
    respone.raise_for_status()
    workspace = respone.json()
    print(workspace['url'])
    return workspace['id']


def create_board(board_name, workspace, prefs_background):
    url = 'https://api.trello.com/1/boards/'    
    query = {
        'name': board_name, 
        'key': trello_key, 
        'token': trello_token, 
        'idOrganization': workspace, 
        'prefs_background': prefs_background
        }
    response = requests.request('POST', url, params=query)
    board_id = response.json()['shortUrl']
    print(board_id)


def trello():
    project =  Project.objects.last()
    project_name = project.title
    project_start = project.start.strftime('%d.%m')
    project_end = project.end.strftime('%d.%m')

    workspace = create_workspace(project_name, project_start, project_end)

    teams = Team.objects.all()
    backgrounds = ['blue', 'orange', 'green', 'red', 'purple', 'pink', 'lime', 'sky', 'grey']
    for team in teams:
          pm_id = team.time.pm_id
          background = backgrounds[pm_id]
          time = str(team.time).split(' ')[1]
          participants = team.participants.all()
          names = ''
          for participant in participants:
              name = participant.student.name.split(' ')[0]
              names = names + ', ' + name
          board_name = time + names
          create_board(board_name, workspace, background)

 