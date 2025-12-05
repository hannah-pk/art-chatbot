from django.urls import path
from . import views

urlpatterns = [
    path("conversations/", views.ConversationListView.as_view(), name="conversations"),
    path("chat/<int:conv_id>/", views.MessageListView.as_view(), name="chat"),
    path("chat/<int:conv_id>/message/", views.MessageCreateView.as_view(), name="create_message"),
]