from django.db import models
from chats.models import Conversation, Image
from django.core.validators import MaxLengthValidator, MinLengthValidator

class Message(models.Model):
    """
    Represents a message in the app

    Contains the message text, the reference to an Image object if it has one and information about whether the message is a user prompt or a chatbot response
    """
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])
    isPrompt = models.BooleanField(default=True)
    image = models.OneToOneField(Image,on_delete=models.SET_NULL, related_name="message",null=True,default=None)

    def __str__(self):
        return self.content