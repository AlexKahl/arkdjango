from django.contrib import admin
from .models import Coach, Student, Lesson


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class CoachInline(admin.StackedInline):
    model = Coach
    can_delete = False
    verbose_name_plural = "Coach"


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = [CoachInline]


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("id", "first_name", "last_name", "phone_number", "level")
    readonly_fields = ("id",)
    search_fields = ("id", "first_name", "last_name", "phone_number", "level")


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "location",
        "type_of_lesson",
        "date",
        "time",
        "status",
        "meeting_point",
        "booking",
    )
    search_fields = (
        "id",
        "coach",
        "location",
        "type_of_lesson",
        "date",
        "time",
        "status",
        "booking"
    )
    filter_horizontal = ('coach', 'participant')

    readonly_fields = ("id",)
    list_filter = ("booking", "location", "type_of_lesson", "date", "time")
