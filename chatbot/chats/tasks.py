from sentence_transformers import SentenceTransformer, util
import torch

INTENTS= {
    "colour_palette":["Please generate a colour palette based off this image", "Create a colour palette around the theme of spring", "Give me a colour scheme for a fight scene"],
    "edit_image":["Could you make the shadows more intense and sad?", "Please enhance the brightness and contrast of this image", "Can you add a vignette effect to this photo?", "Make the colors more vibrant and saturated", "This image looks a bit flat, how can i fix it?"],
}

MOODS = {
    "happy": ["bright", "vibrant", "colorful", "cheerful", "lively"],
    "sad": ["muted", "dark", "somber", "gloomy", "dull"],
    "angry": ["intense", "fiery", "bold", "aggressive", "strong"],
    "calm": ["soft", "pastel", "tranquil", "peaceful", "serene"]
}

MODEL = SentenceTransformer('all-MiniLM-L6-v2')

examples = []
example_to_intent = []

for intent, example_list in INTENTS.items():
    for example in example_list:
        examples.append(example)
        example_to_intent.append(intent)

example_embeddings = MODEL.encode(examples,normalize_embeddings=True)

def get_response(message):
    temp_response = "responding to " + message
    return temp_response

def process_request(message):
    threshold = 0.6
    message_embedding = MODEL.encode([message],normalize_embeddings=True)
    scores = util.cos_sim(message_embedding, example_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    if best_score >= threshold:
        return example_to_intent[best_idx]

    response = get_response(message)
    return response

while True:
    i = input("Enter your message: ")
    print(process_request(i))