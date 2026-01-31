from sentence_transformers import SentenceTransformer, util
import torch
from django.core.management.base import BaseCommand
import os

output_dir = 'embeddings'
os.makedirs(output_dir,exist_ok=True)

INTENTS= {
    "colour_palette":["Please generate a colour palette based off this image", "Create a colour palette around the theme of spring", "Give me a colour scheme for a fight scene"],
    "edit_image":["Could you make the shadows more intense and sad?", "Please enhance the brightness and contrast of this image", "Can you add a vignette effect to this photo?", "Make the colors more vibrant and saturated", "This image looks a bit flat, how can i fix it?"],
}

MOODS = {
    "happy": ["bright", "vibrant", "cheerful", "lively", "joyful", "jubilant", "merry"],
    "sad": ["muted", "dark", "somber", "gloomy", "dull", "melancholy", "depressing", "dreary", "wistful"],
    "angry": ["intense", "fiery", "bold", "aggressive", "strong", "striking", "cantankerous", "fierce"],
    "calm": ["soft", "pastel", "tranquil", "peaceful", "serene", "soothing", "relaxing", "gentle"],
}

class Command(BaseCommand):
    help = 'Train the language model for the chatbot and save the required models into external files'

    def handle(self, *args, **options):
        MODEL = SentenceTransformer('all-MiniLM-L6-v2')

        examples = []
        example_to_intent = []

        for intent, example_list in INTENTS.items():
            for example in example_list:
                examples.append(example)
                example_to_intent.append(intent)

        example_embeddings = MODEL.encode(examples,normalize_embeddings=True)

        torch.save({
            'labels': example_to_intent,
            'embeddings': example_embeddings,
            'model': 'all-MiniLM-L6-v2',
            'type': 'intent_examples',
        },
        os.path.join(output_dir,'intent.pt')
        )

        mood_names = []
        mood_embeddings = []

        for mood, synonyms in MOODS.items():
            emb= MODEL.encode(synonyms,normalize_embeddings=True, convert_to_tensor=True)
            centroid = emb.mean(dim=0)
            mood_embeddings.append(centroid)
            mood_names.append(mood)
        mood_embeddings = torch.stack(mood_embeddings)

        torch.save({
            'labels': mood_names,
            'embeddings': mood_embeddings,
            'model': 'all-MiniLM-L6-v2',
            'type': 'mood_examples',
        },
        os.path.join(output_dir,'mood.pt')
        )