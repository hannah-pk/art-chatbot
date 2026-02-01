from django.db import models
from chats.models import Conversation
from django.core.validators import RegexValidator, MaxLengthValidator, MinLengthValidator

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])
    isPrompt = models.BooleanField(default=True)
    image = models.ImageField(upload_to='temp_images/', null=True, blank=True)

    def __str__(self):
        return self.content