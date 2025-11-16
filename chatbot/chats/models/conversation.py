from django.db import models
from chats.models import User

class Conversation(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(auto_now_add=True)