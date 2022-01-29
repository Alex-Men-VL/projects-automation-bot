from django.contrib import admin
from telegram_bot.management.commands.sort import sort_and_create_teams
from telegram_bot.models import Team

from .models import (
    Student,
    StudentLevel,
    ProductManager,
    Time,
    Project,
    Participant,
    Team
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    exclude = ('bot_state', 'chat_id')
    readonly_fields = ('tg_username',)


@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    pass


class TimeInline(admin.TabularInline):
    model = Time


@admin.register(ProductManager)
class ProductManagerAdmin(admin.ModelAdmin):
    exclude = ('bot_state', 'chat_id')
    readonly_fields = ('tg_username',)
    inlines = (TimeInline,)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    actions = ['create_teams']

    @admin.action(description='Сформировать команды из участников')
    def create_teams(self, request, queryset):
        if Team.objects.all():
            text = 'Команды уже были сформированны ранее. Проверьте разде "Команды"'
            self.message_user(request, text)
        else:
            sort_and_create_teams()
            self.message_user(request, 'Команды можно посмотреть в разделе "Команды"')



class ParticipantInline(admin.TabularInline):
    model = Participant


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = (ParticipantInline,)


