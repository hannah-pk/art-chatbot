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


class MessageSerialiser(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = ["id", "conversation", "content", "isPrompt", "created_at"]

class ConversationSerialiser(serializers.ModelSerializer):
    messages = MessageSerialiser(many=True, read_only=True)
    class Meta:
        model = Conversation
        fields = ["id","title","created_at","user_identity"]
        extra_kwargs = {"user_identity": {"read_only": True}}
    