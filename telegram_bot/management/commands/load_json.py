import logging
from django.core.management import BaseCommand
from telegram_bot.models import Student, ProductManager, StudentLevel, Time
import datetime
import json

    
class Command(BaseCommand):
      def add_arguments(self, parser):
        parser.add_argument('-f', '--file', type=str, help='Название файла JSON')

      def handle(self, *args, **kwargs):
            file = kwargs['file']
            if file:
                  file = f'{file}.json'
            else:
                  file = 'file.json'
            try:
                  load_json(file)
            except Exception as error:
                  logging.error(error)


def load_json(file):
      with open(file, 'r', encoding='utf-8') as file:
            file = json.load(file)
      for group in file:
            if group == 'PM':
                  pm_group = file[group]
                  for pm in pm_group:
                        name = pm.get('name')
                        tg_username = pm.get('tg_username')
                        discord_username = pm.get('discord_username')
                        time_slots = pm.get('time_slots')

                        pm, _ = ProductManager.objects.get_or_create(
                              name = name,
                              tg_username = tg_username,
                              discord_username = discord_username,
                              )
                        pm.save()

                        for time_slot in time_slots:
                              time_slot = datetime.datetime.strptime(time_slot, "%H:%M")
                              timeslot, _ = Time.objects.get_or_create(
                                    time_interval = time_slot, pm = pm)                       
                              timeslot.save()

            if group == 'Student':
                  student_group = file[group]
                  for student in student_group:
                        name = student.get('name')
                        tg_username = student.get('tg_username')
                        discord_username = student.get('discord_username')
                        student_level = student.get('level')

                        level, _ = StudentLevel.objects.get_or_create(
                              name = student_level)
                        level.save()
                        
                        student, _ = Student.objects.get_or_create(
                              name = name,
                              tg_username = tg_username,
                              discord_username = discord_username,
                              )
                        student.level = level
                        student.save()
                              
                        
                        

                        
                    

                        

      