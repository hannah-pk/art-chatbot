from sentence_transformers import SentenceTransformer
from django.core.management.base import BaseCommand
from django.apps import apps
from os import path

class Command(BaseCommand):
    help = 'Load the language model into local files'
    def handle(self, *args, **options):
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        app_path = apps.get_app_config("chats").path
        model_path = path.join(app_path,"miniLM")
        model.save(model_path)
        
