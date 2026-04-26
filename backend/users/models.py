from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        MERCHANT = "merchant", "Merchant"
        REVIEWER = "reviewer", "Reviewer"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)

    REQUIRED_FIELDS = ["email", "role"]

    def __str__(self):
        return f"{self.username} ({self.role})"
