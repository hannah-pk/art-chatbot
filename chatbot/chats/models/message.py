from django.db import models
from chats.models import Conversation, Image
from django.core.validators import MaxLengthValidator, MinLengthValidator

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])
    isPrompt = models.BooleanField(default=True)
    image = models.OneToOneField(Image,on_delete=models.SET_NULL, related_name="message",null=True,default=None)

    def __str__(self):
        return self.content
    
    def delete(self):
        if self.image is not None:
            self.image.delete() #makes sure that a related image is completely deleted from any databases
        super().delete()