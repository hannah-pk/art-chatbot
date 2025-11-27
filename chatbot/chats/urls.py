from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.ConversationListView.as_view(), name= "conversations")
]