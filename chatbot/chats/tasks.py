from sentence_transformers import SentenceTransformer, util
import torch
from nltk import pos_tag, word_tokenize
#from nltk.corpus import stopwords

#stop_words = set(stopwords.words('english'))
KEEP_TAGS = {"JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS"}

def filter_common_words(text):
    words = text.lower().split()
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(filtered_words)

def extract_relevant_words(text):
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)
    relevant_words = [word for word, tag in tagged if tag in KEEP_TAGS]
    return ' '.join(relevant_words)

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

MODEL = SentenceTransformer('all-MiniLM-L6-v2')

examples = []
example_to_intent = []

for intent, example_list in INTENTS.items():
    for example in example_list:
        examples.append(example)
        example_to_intent.append(intent)

example_embeddings = MODEL.encode(examples,normalize_embeddings=True)

mood_names = []
mood_embeddings = []

for mood, synonyms in MOODS.items():
    emb= MODEL.encode(synonyms,normalize_embeddings=True, convert_to_tensor=True)
    centroid = emb.mean(dim=0)
    mood_embeddings.append(centroid)
    mood_names.append(mood)
mood_embeddings = torch.stack(mood_embeddings)

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

def deduce_mood(message):
    threshold = 0.5
    filtered_message = extract_relevant_words(message)
    print(filtered_message)
    words = filtered_message.split()
    mood = 'unknown'
    highscore = 0
    for word in words:
        word_embedding = MODEL.encode([word],normalize_embeddings=True)
        word_scores = util.cos_sim(word_embedding, mood_embeddings)[0]
        best_idx = word_scores.argmax().item()
        best_score = word_scores[best_idx].item()
        best_mood = mood_names[best_idx]
        if best_score >= max(threshold,highscore):
            mood = best_mood
            highscore = best_score
            
    #message_embedding = MODEL.encode(filtered_message,normalize_embeddings=True)
    #scores = util.cos_sim(message_embedding, mood_embeddings)[0]
    #best_idx = scores.argmax().item()
    """     best_mood = mood_names[best_idx]
    if scores[best_idx].item() >= threshold:
        return best_mood """
    return mood

while True:
    i = input("Enter your message: ")
    print(deduce_mood(i))