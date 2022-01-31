# Распределение участников по проектам с Django админкой
Бот позволяет загрузить данные об участниках в формате json,
провести опрос о желаемом времени созвона для проекта среди студентов,
и автоматически распредлить их по группам в зависимости от уровня студента
и времени созвона. Каждая группа будет назначена на свободный интервал
времени среди продакт менеджеров. Для каждой группы будет сформирована 
Trello доска.

## Необходимое окружение
Для работы скриптов необходимо получить токен и ключ на сайте [trello](https://trello.com/app-key)  
и присвоить их переменным окружения в файле .env в корневом каталоге:
```
TRELLO_KEY=Ваш ключ trello
TRELLO_TOKEN=Ваш токен trello
```
Прочие переменные окружения:
```
TELEGRAM_BOT_TOKEN=Токен бота в Телеграм
DEVS_CHAT_ID=ID вашего чата в Телеграм
```

## Как установить
* Клонируем репозиторий
* Создаем виртуальное окружение
* В корень проекта добавляем .env c требуемыми переменными
* Устанавливаем зависимости
```
pip install -r requirements.txt
```
* Выполняем миграции
```
python manage.py migrate
```
* Создаем суперпользователя для админки
```
python manage.py createsuperuser
```

## Использование
В корневом каталоге необходимо создать файл file.json с данными продакт менеджеров и студентов в формате:
```
{
      "PM": [
                  {
                        "name": "Тим",
                        "tg_username": "example",
                        "discord_username": "example",
                        "time_slots": ["18:00", "18:30", "19:00", "19:30", "20:00"]
                  },
            ],
      "Student": [
                  {
                        "name": "Александр Попов",
                        "level": "junior",
                        "tg_username": "example",
                        "discord_username": "example"
                  },
        ]
}
   ```

Для загрузки данных из файла в БД используйте команду:
```
python manage.py load_json
```
Если название вашего файла другое, используйте аргументы:
```
python manage.py load_json --file название вашего файла
```

Запускаем бота
```
python manage.py startbot
```
После запуска бота каждому студенту придет уведомление с предложением выбрать
желаемый временной слот. Далее за пять дней до проекта произойдет формирование
групп из студентов и пм-ов. Студетам, которым не досталось удобного для них
временного слота бот предложит выбрать из оставшихся или записаться на другую
неделю.

Формирование групп можно запустить самостоятельно из админки в разделе "участники".



### Цель проекта
Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).
