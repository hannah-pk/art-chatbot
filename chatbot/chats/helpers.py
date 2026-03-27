from .models import Conversation
from django.shortcuts import get_object_or_404
import torch

#establishes identity for user's conversation based on whether they are logged in or not
def get_identity(request): 
    if request.user.is_authenticated:
        return f"user:{request.user.id}"
    
    if not request.session.session_key:
        request.session.create()
    return f"anon:{request.session.session_key}"

def get_embeddings(file_name):
    data = torch.load(file_name,weights_only=False)
    return data['labels'],data['embeddings']