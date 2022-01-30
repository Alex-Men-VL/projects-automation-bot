from django.contrib import admin, messages
from django.contrib.admin import SimpleListFilter
from django.db.models import Count

from .collect_teams import sort_and_create_teams
from .models import (Participant, ProductManager, Project, Student,
                     StudentLevel, Team, Time)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    exclude = ('bot_state', 'chat_id')
    search_fields = ('name', 'tg_username')


@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    pass


class TimeInline(admin.TabularInline):
    model = Time


@admin.register(ProductManager)
class ProductManagerAdmin(admin.ModelAdmin):
    exclude = ('bot_state', 'chat_id')
    search_fields = ('name', 'tg_username')
    inlines = (TimeInline,)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    readonly_fields = ('workspace_id',)


class TeamExistenceFilter(SimpleListFilter):
    title = 'Участник в команде'
    parameter_name = 'team'

    def lookups(self, request, model_admin):
        return [
            ("in_team", "В команде"),
            ("not_in_team", "Не в команде"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "in_team":
            return queryset.filter(team__isnull=False)
        if self.value():
            return queryset.distinct().filter(team__isnull=True)


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_filter = (TeamExistenceFilter,)
    list_display = ('student', 'get_participant_level', 'project')
    search_fields = ('student__name', 'student__tg_username')
    actions = ('create_teams',)

    @admin.action(description='Сформировать команды из участников')
    def create_teams(self, request, queryset):
        if Team.objects.filter(project=Project.objects.last()).exists():
            text = '''Команды уже были сформированы ранее.
            Проверьте разделе "Команды"'''
            self.message_user(request, text, messages.ERROR)
        else:
            sort_and_create_teams()
            text = 'Команды можно посмотреть в разделе "Команды"'
            self.message_user(request, text, messages.SUCCESS)

    @admin.display(description='Уровень')
    def get_participant_level(self, obj):
        return obj.student.level


class ParticipantInline(admin.TabularInline):
    model = Participant


class ParticipantCountFilter(SimpleListFilter):
    title = 'Количество участников'
    parameter_name = 'participant'

    def lookups(self, request, model_admin):
        return [
            ("three", "Трое"),
            ("two", "Двое"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "three":
            return queryset.annotate(
                participants_count=Count('participants')
            ).filter(participants_count__exact=3)
        if self.value():
            return queryset.annotate(
                participants_count=Count('participants')
            ).filter(participants_count__exact=2)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = (ParticipantInline,)
    list_filter = (ParticipantCountFilter, 'time__pm')
    list_display = ('title', 'get_participants_level', 'project')

    @admin.display(description='Уровень')
    def get_participants_level(self, obj):
        levels = set(pt.student.level.name for pt in obj.participants.all())
        levels_str = ', '.join(list(levels))
        return levels_str
