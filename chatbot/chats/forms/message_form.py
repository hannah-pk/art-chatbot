from django import forms
from chats.models import Message, Conversation

class MessageForm(forms.ModelForm):
    """Form enabling a user to send a message to the chatbot"""
    class Meta:
        models = Message
        fields = ["content"]
    
    def __init__(self, conversation=None, user=None):
        super().__init__()
        if conversation:
            self.conversation = conversation
        else:
            self.conversation = Conversation.objects.create(
                user = user
            )