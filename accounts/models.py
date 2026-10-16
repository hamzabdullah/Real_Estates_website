
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        AGENT = 'AGENT', 'Agent'
        CLIENT = 'CLIENT', 'Client'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CLIENT
    )

    phone = models.CharField(
        max_length=20,
        blank=True
    )

    def __str__(self):
        return self.username
