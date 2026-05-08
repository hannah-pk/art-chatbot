import numpy as np
from django.apps import apps
import torch
import json
import cloudinary.utils
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ONNX_MODEL_PATH = str(BASE_DIR / 'onnx_model')
app_path = apps.get_app_config("chats").path
tokenizer = None
model = None

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

def get_tokenizer():
    global tokenizer
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(ONNX_MODEL_PATH)
    return tokenizer

def get_model():
    global model
    if model is None:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        model = ORTModelForFeatureExtraction.from_pretrained(ONNX_MODEL_PATH)
    return model

def encode(texts, normalize=True):
    inputs = get_tokenizer()(texts, return_tensors='np', padding=True, truncation=True)
    outputs = get_model()(**inputs)
    embeddings = outputs.last_hidden_state.mean(axis=1)
    if normalize:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
    return embeddings