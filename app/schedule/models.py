from django.contrib.auth.models import User
from django.db import models
from django.conf import settings

JOB_TITLES = (
    ('INTERN', "INTERN"),
    ('JUNIOR', 'JUNIOR'),
    ('SENIOR', 'SENIOR'),
    ('MANAGEMENT', 'MANAGEMENT'),
)

MEETING_POINTS = (("SCHOOL", "SCHOOL"), ("RATURE CAMP", "RATURE CAMP"),
                  ("AT THE BEACH", "AT THE BEACH"))

LOCATIONS = (
    ('FOZ DO LIZANDRO', "FOZ DO LIZANDRO"),
    ('PRAIA DO SUL', 'PRAIA DO SUL'),
    ('PRAIA DO NORTE', 'PRAIA DO NORTE'),
    ('MATADURO', 'MATADURO'),
    ('RIBERA', 'RIBERA'),
)

LESSON_TYPES = (
    ('BEGINNER', "BEGINNER"),
    ('INTERMEDIATE', 'INTERMEDIATE'),
    ('ADVANCED', 'ADVANCED'),
    ('PRIVATE', 'PRIVATE'),
)

SURF_LEVELS = (
    ('BEGINNER', "BEGINNER"),
    ('INTERMEDIATE', 'INTERMEDIATE'),
    ('ADVANCED', 'ADVANCED'),
)

LESSON_STATI = (
    ('LIVE', 'LIVE'),
    ('CANCELED', 'CANCELED'),
)

BOOKING_TYPES = (('3 Surfers', '3 Surfers'),
                 ('Rapture', 'Rapture'),)


class Student(models.Model):

    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=150, null=False)
    last_name = models.CharField(max_length=10, null=True)
    birth_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)
    level = models.CharField(max_length=50, choices=SURF_LEVELS, null=False)
    is_regular = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Coach(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    job_title = models.CharField(
        max_length=50, choices=JOB_TITLES, default="JUNIOR")
    is_active = models.BooleanField(default=True)
    is_surfcoach = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}"


class Lesson(models.Model):

    id = models.AutoField(primary_key=True)
    coach = models.ManyToManyField(Coach)
    location = models.CharField(max_length=50, choices=LOCATIONS, null=False)
    type_of_lesson = models.CharField(
        max_length=50, choices=LESSON_TYPES, null=False)
    date = models.DateField(null=False, blank=False)
    time = models.TimeField(null=False, blank=False)

    status = models.CharField(
        max_length=50, choices=LESSON_STATI, null=False, default="LIVE")

    meeting_point = models.CharField(
        max_length=50, choices=MEETING_POINTS, null=False, default="SCHOOL")

    booking = models.CharField(
        max_length=50, choices=BOOKING_TYPES, null=False, default="3 Surfers")

    participant = models.ManyToManyField(Student, blank=True)

    number_of_participants = models.IntegerField(blank=True, null=True)

    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.booking}: {self.type_of_lesson} - {self.location}: {self.date} - {self.time}'

    class Meta:
        unique_together = ("booking", "location",
                           "type_of_lesson", "date", "time")
