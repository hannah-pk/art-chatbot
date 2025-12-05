from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Conversation, Message
from rest_framework import generics, status
from rest_framework.response import Response
from .serialisers import UserSerialiser, ConversationSerialiser, MessageSerialiser
from rest_framework.permissions import IsAuthenticated, AllowAny
from .helpers import get_identity, get_or_create_conversation
from .tasks import get_response

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerialiser
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # log serializer errors for debugging registration failures
            print("Register serializer errors:", serializer.errors)
        return super().create(request, *args, **kwargs)

class ConversationListView(generics.ListCreateAPIView):
    serializer_class = ConversationSerialiser
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_identity = get_identity(self.request)
        return Conversation.objects.filter(user_identity=user_identity)
    
    def perform_create(self, serializer):
        user_identity = get_identity(self.request)
        serializer.save(user_identity=user_identity)
    
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerialiser
    permission_classes = [AllowAny]

    def get_queryset(self):
        conversation = get_or_create_conversation(self.request, conv_id=self.kwargs['conv_id'])
        return Message.objects.filter(conversation=conversation)
    
class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerialiser
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        conversation = get_or_create_conversation(self.request, conv_id=self.kwargs['conv_id'])
        
        # Save user's message
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(conversation=conversation, isPrompt=True)
        
        # Get AI response
        response = get_response(request.data.get("content"))
        
        # Save AI response
        response_message = Message(
            conversation=conversation,
            content=response,
            isPrompt=False,
        )
        response_message.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                "user_message": serializer.data,
                "response": response,
                "response_message": MessageSerialiser(response_message).data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )



        
    
    