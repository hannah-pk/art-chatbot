from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="conversations")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title