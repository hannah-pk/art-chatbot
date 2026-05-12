import torch
from django.core.management.base import BaseCommand
import os
from chats.helpers import read_json, encode

output_dir = 'embeddings'
os.makedirs(output_dir,exist_ok=True)

examples_file= 'mappings/prompt_examples.json'
moods_file = 'mappings/mood_synonyms.json'

INTENTS= read_json(examples_file)
MOODS = read_json(moods_file)    


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

        example_embeddings = encode(examples,normalize_embeddings=True)
    
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
        mood_embeddings= encode(syn,normalize_embeddings=True, convert_to_tensor=True)
        torch.save({
            'labels': synonyms_to_moods,
            'embeddings': mood_embeddings,
        },
        os.path.join(output_dir,'mood.pt')
        )

