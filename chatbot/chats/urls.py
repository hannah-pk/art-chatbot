from django.urls import path
from . import views

urlpatterns = [
    path("conversations/", views.ConversationListView.as_view(), name="conversations"),
    path("conversations/<int:conv_id>/", views.ConversationUpdateView.as_view(), name="conversation_update"),
    path("conversations/<int:conv_id>/delete/", views.ConversationDeleteView.as_view(), name="conversation_delete"),
    path("chat/<int:conv_id>/", views.MessageListView.as_view(), name="chat"),
    path("chat/<int:conv_id>/message/", views.MessageCreateView.as_view(), name="create_message"),
    path("init/",views.init_session,name="initialise_session")
]