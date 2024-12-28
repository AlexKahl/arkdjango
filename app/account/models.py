from django.db import models
from django.conf import settings

ROLE_CHOICES = (
    (1, 'Admin'),
    (2, 'Management'),
    (3, 'Coach'),
)


class Profile(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.PositiveSmallIntegerField(
        choices=ROLE_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"Profile for user: {self.user.username}"
