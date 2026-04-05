from django.contrib import admin
from .models import Conversation, Message, Request

# Register your models here.
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for conversations"""
    list_display=[
        "title","user_identity","created_at","get_messages"
    ]
    
    def get_messages(self,conv):
        return list(Message.objects.filter(conversation=conv))

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for messages"""
    list_display=[
        "conversation","created_at","content","isPrompt","image","get_user"
    ]
    def get_user(self,message):
        return message.conversation.user_identity
    
@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    """Admin interface for ongoing requests"""
    list_display=[
        "conversation","instruction","needs_image","params"
    ]