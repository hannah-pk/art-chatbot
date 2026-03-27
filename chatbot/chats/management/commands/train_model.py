from sentence_transformers import SentenceTransformer, util
import torch
from django.core.management.base import BaseCommand
import os
from chats.helpers import read_json

output_dir = 'embeddings'
os.makedirs(output_dir,exist_ok=True)

mappings_dir = 'mappings'
examples_file= os.path.join(mappings_dir,'prompt_examples.json') 
moods_file = os.path.join(mappings_dir,'mood_synonyms.json')

INTENTS= read_json(examples_file)
MOODS = read_json(moods_file)

#IMAGE_REQUESTS = ["Please generate a colour palette based off this image", "How can i make this drawing look more cheerful?", "Please make this look darker" ]
    


class Command(BaseCommand):
    help = 'Train the language model for the chatbot and save the required models into external files'

    def add_arguments(self, parser):
        parser.add_argument(
            "--instructions",
            action='store_true'
        )
        parser.add_argument(
            "--mood",
            action="store_true"
        )

    def handle(self, *args, **options):
        self.MODEL = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        instruction = options["instructions"]
        mood = options["mood"]
        if instruction:
            self.train_instructions()
        if mood:
            self.train_mood()

    def train_instructions(self):
        examples = []
        example_to_intent = []

        for intent, example_list in INTENTS.items():
            for example in example_list:
                examples.append(example)
                example_to_intent.append(intent)

        example_embeddings = self.MODEL.encode(examples,normalize_embeddings=True)
    
        torch.save({
            'labels': example_to_intent,
            'embeddings': example_embeddings,
        },
        os.path.join(output_dir,'intent.pt')
        )

    def train_mood(self):
        syn = []
        synonyms_to_moods = []
        mood_embeddings = []

        for mood, synonyms in MOODS.items():
            for synonym in synonyms:
                syn.append(synonym)
                synonyms_to_moods.append(mood)
        mood_embeddings= self.MODEL.encode(syn,normalize_embeddings=True, convert_to_tensor=True)
            # centroid = emb.mean(dim=0)
            # mood_embeddings.append(centroid)
            # mood_names.append(mood)
        #mood_embeddings = torch.stack(mood_embeddings)
        torch.save({
            'labels': synonyms_to_moods,
            'embeddings': mood_embeddings,
        },
        os.path.join(output_dir,'mood.pt')
        )

        #image_param_embeddings = MODEL.encode(IMAGE_REQUESTS, normalize_embeddings=True,convert_to_tensor=True)

        #torch.save({
        #    'embeddings': image_param_embeddings,
        #    'model': 'all-MiniLM-L6-v2',
        #    'type': 'image_requests',
        #},
        #os.path.join(output_dir,'image.pt')
        #)

