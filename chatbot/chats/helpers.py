from .models import Conversation
from django.shortcuts import get_object_or_404
from django.apps import apps
import torch
import json
import cloudinary.utils
import time

app_path = apps.get_app_config("chats").path

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

def read_json(file_name):
    file_path = app_path+"/"+file_name
    with open(file_path,'r') as f:
        data = json.load(f)
    return data

def get_signed_url(image,expires_in=300):
    url,_=cloudinary.utils.cloudinary_url(
        image.public_id,
        type="authenticated",
        sign_url=True,
        secure=True,
        expires_at=int(time.time())+expires_in
    )
    return url