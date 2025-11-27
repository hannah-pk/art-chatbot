from .models import Conversation
from django.shortcuts import get_object_or_404

#establishes identity for user's conversation based on whether they are logged in or not
def get_identity(request): 
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    
    if not request.session.session_key:
        request.session.create()
    return f"anon:{request.session.session_key}"

def get_or_create_conversation(request, conv_id=None):
    identity = get_identity(request)

    if conv_id:
        return get_object_or_404(Conversation,id=conv_id,user_identity=identity)
    return Conversation.objects.create(user_identity=identity)