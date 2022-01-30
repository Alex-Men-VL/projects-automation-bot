from django.db import models


class User(models.Model):
    name = models.CharField(
        'имя',
        max_length=20,
        db_index=True
    )
    tg_username = models.CharField(
        'ник в Telegram',
        max_length=100,
        unique=True
    )
    discord_username = models.CharField(
        'ник в Discord',
        max_length=100,
        unique=True
    )
    bot_state = models.CharField(
        'текущее состояния бота',
        max_length=100,
        blank=True,
        null=True
    )
    chat_id = models.IntegerField(
        'Chat ID в Telegram',
        null=True,
        blank=True
    )

    class Meta:
        abstract = True


class Student(User):
    level = models.ForeignKey(
        'StudentLevel',
        verbose_name='уровень ученика',
        related_name='students',
        on_delete=models.SET_NULL,
        null=True,
    )

    class Meta:
        verbose_name = 'ученик'
        verbose_name_plural = 'ученики'

    def __str__(self):
        return f'{self.name} {self.tg_username}'


class StudentLevel(models.Model):
    name = models.CharField(
        'название уровня',
        max_length=20,
    )

    class Meta:
        verbose_name = 'уровень'
        verbose_name_plural = 'уровни'

    def __str__(self):
        return f'{self.name}'


class ProductManager(User):

    class Meta:
        verbose_name = 'продукт-менеджер'
        verbose_name_plural = 'продукт-менеджеры'

    def __str__(self):
        return f'{self.name}'


class Time(models.Model):
    pm = models.ForeignKey(
        ProductManager,
        verbose_name='продукт-менеджер',
        related_name='call_times',
        on_delete=models.CASCADE
    )
    time_interval = models.TimeField(
        'начало промежутка времени'
    )

    class Meta:
        verbose_name = 'промежуток времени'
        verbose_name_plural = 'промежутки времени'
        ordering = ('pm__name', 'time_interval')

    def __str__(self):
        return f'{self.pm.name} {self.time_interval}'


class Project(models.Model):
    title = models.CharField(
        'название проекта',
        max_length=100
    )
    description = models.TextField(
        'описание проекта',
        blank=True,
        null=True
    )
    link = models.URLField(
        'Ссылка на задание',
        blank=True,
        null=True
    )
    start = models.DateTimeField(
        'Дата начала проекта',
        blank=False,
        null=False
    )
    end = models.DateTimeField(
        'Дата окончания проекта',
        blank=False,
        null=False
    )
    workspace_id = models.CharField(
        'ID рабочего пространства Trello',
        max_length=30,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'проект'
        verbose_name_plural = 'проекты'

    def __str__(self):
        return f'{self.title} {self.start.strftime("%d.%m.%Y")} - ' \
               f'{self.end.strftime("%d.%m.%Y")}'


class Participant(models.Model):
    student = models.OneToOneField(
        Student,
        verbose_name='ученик',
        related_name='participant',
        on_delete=models.CASCADE
    )
    project = models.ForeignKey(
        Project,
        verbose_name='проект',
        related_name='participants',
        on_delete=models.SET_NULL,
        null=True,
    )
    team = models.ForeignKey(
        'Team',
        verbose_name='команда',
        related_name='participants',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    times = models.ManyToManyField(
        Time,
        verbose_name='выбранное время',
        related_name='participants',
    )

    class Meta:
        verbose_name = 'участник'
        verbose_name_plural = 'участники'

    def __str__(self):
        return f'{self.student.name} {self.student.tg_username}'


class Team(models.Model):
    title = models.CharField(
        'название команды',
        max_length=200
    )
    project = models.ForeignKey(
        Project,
        verbose_name='проект',
        related_name='teams',
        on_delete=models.CASCADE,
        null=True
    )
    time = models.OneToOneField(
        Time,
        verbose_name='временной интервал',
        related_name='team',
        on_delete=models.CASCADE
    )
    trello_link = models.URLField(
        'ссылка на Trello-доску',
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = 'команда'
        verbose_name_plural = 'команды'
        ordering = ('time__pm__name', 'time__time_interval')

    def __str__(self):
        return f'{self.title}'
