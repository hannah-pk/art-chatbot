from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serialisers import UserSerialiser
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerialiser
    permission_classes = [AllowAny]