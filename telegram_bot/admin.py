from django.contrib import admin


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
    exclude = ('bot_state',)


@admin.register(StudentLevel)
class StudentLevelAdmin(admin.ModelAdmin):
    pass


class TimeInline(admin.TabularInline):
    model = Time


@admin.register(ProductManager)
class ProductManagerAdmin(admin.ModelAdmin):
    exclude = ('bot_state',)
    inlines = (TimeInline,)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    pass


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    pass


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    pass


class ParticipantInline(admin.TabularInline):
    model = Participant


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    inlines = (ParticipantInline,)
