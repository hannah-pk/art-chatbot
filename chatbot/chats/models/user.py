from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Model used for user authentication."""
    email = models.EmailField(unique=True, blank=False)