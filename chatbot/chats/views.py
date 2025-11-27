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

class ConversationListView(generics.ListCreateAPIView):
    serializer_class = ConversationSerialiser
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_anonymous:
            return Conversation.objects.none()
        return Conversation.objects.filter(user=user)
    
    def perform_create(self, serializer):
        if serializer.is_valid():
            user_id = get_identity(self.request)
            serializer.save(user_identity = user_id)
        else: 
            print(serializer.errors)
    
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerialiser
    permission_classes = [AllowAny]

    def get_queryset(self):
        conversation = get_or_create_conversation(self.request,conv_id=self.kwargs['conversation_id'])
        return Message.objects.filter(conversation=conversation)
    
class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerialiser

    def perform_create(self, serializer):
        conversation = get_or_create_conversation(self.request,self.kwargs['conversation_id'])
        serializer.save(conversation=conversation, isPrompt=True)
        response = get_response(self.request.data.get("content"))
        return response,conversation.id

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response,conv_id = self.perform_create(serializer)


        message = Message(
            conversation = Conversation.objects.get(conv_id),
            content = response,
            isPrompt = False,
        )
        message.save()

        headers = self.get_success_headers(serializer.data)
        return Response({"response":response},status=status.HTTP_200_OK, headers=headers)



        
    
    