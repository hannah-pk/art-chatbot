from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Conversation, Message
from rest_framework import generics, status
from rest_framework.response import Response
from .serialisers import UserSerialiser, ConversationSerialiser, MessageSerialiser
from rest_framework.permissions import IsAuthenticated, AllowAny
from .helpers import get_identity
from .tasks import process_request

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

class ConversationDeleteView(generics.DestroyAPIView):
    serializer_class = ConversationSerialiser
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user_identity=get_identity(self.request))

    def delete(self, request, *args, **kwargs):
        conversation = get_object_or_404(Conversation, id=self.kwargs['conv_id'])
        self.perform_destroy(conversation)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConversationUpdateView(generics.UpdateAPIView):
    serializer_class = ConversationSerialiser
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user_identity=get_identity(self.request))

    def patch(self, request, *args, **kwargs):
        conversation = get_object_or_404(Conversation, id=self.kwargs['conv_id'], user_identity=get_identity(request))
        serializer = self.get_serializer(conversation, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerialiser
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Only allow access if the conversation belongs to the current identity
        identity = get_identity(self.request)
        conversation = get_object_or_404(Conversation, id=self.kwargs['conv_id'], user_identity=identity)
        return Message.objects.filter(conversation=conversation)
    
class MessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerialiser
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        identity = get_identity(self.request)
        conv_id = self.kwargs['conv_id']
        conversation = get_object_or_404(Conversation, id=conv_id, user_identity=identity)

        # Save user's message
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Message serializer errors:", serializer.errors)
        serializer.is_valid(raise_exception=True)
        user_message = serializer.save(conversation=conversation, isPrompt=True)

        # Extract image if provided
        image_file = request.FILES.get('image', None)

        # Get AI response (image is passed but not stored long-term)
        response = process_request(request.data.get("content"), conversation, image_file)

        # Save AI response (without storing the image)
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



        
    
    