from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Conversation, Message

class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","password"]
        extra_kwargs = {"password":{"write_only":True}}
    
    def create(self, validated_data):
        user = User.objects.create(**validated_data)
        return user
    
class ConversationSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id","title","created_at","user"]
        extra_kwargs = {"user":{"read_only":True}}

class MessageSerialiser(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "content", "isPrompt", "created_at"]
    