from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Conversation, Message, Image

class UserSerialiser(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","username","password"]
        extra_kwargs = {"password":{"write_only":True}}
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists")
        return value

    def create(self, validated_data):
        username = validated_data.get('username')
        password = validated_data.get('password')
        # Use create_user to ensure password is hashed correctly
        user = User.objects.create_user(username=username, password=password)
        return user

class ImageSerialiser(serializers.ModelSerializer):
    class Meta:
        model =Image
        fields=["url"]

class MessageSerialiser(serializers.ModelSerializer):
    image = ImageSerialiser(required=False,allow_null=True)
    class Meta:
        model = Message
        fields = ["id", "conversation", "content", "isPrompt", "created_at", "image"]
        extra_kwargs = {
            "conversation": {"read_only": True}
        }

class ConversationSerialiser(serializers.ModelSerializer):
    messages = MessageSerialiser(many=True, read_only=True)
    class Meta:
        model = Conversation
        fields = ["id","title","created_at","user_identity","messages"]
        extra_kwargs = {"user_identity": {"read_only": True}}

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.save()
        return instance
    