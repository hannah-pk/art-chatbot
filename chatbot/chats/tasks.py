from sentence_transformers import SentenceTransformer, util
import torch
from nltk import pos_tag, word_tokenize
from chats.models import Request
#from nltk.corpus import stopwords

#stop_words = set(stopwords.words('english'))
KEEP_TAGS = {"JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS"}
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

example_data = torch.load('../embeddings/intent.pt')
example_labels = example_data['labels']
example_embeddings = example_data['embeddings']

mood_data = torch.load('../embeddings/mood.pt')
mood_labels = mood_data['labels']
mood_embeddings = mood_data['embeddings']

image_param_data = torch.load('../embeddings/image.pt')
image_param_embeddings = image_param_data['embeddings']

def filter_common_words(text):
    words = text.lower().split()
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(filtered_words)

def extract_relevant_words(text):
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens)
    relevant_words = [word for word, tag in tagged if tag in KEEP_TAGS]
    return ' '.join(relevant_words)

def get_response(message):
    temp_response = "responding to " + message
    return temp_response

def process_request(message,conv_id):
    r = Request.objects.get_or_create(conversation_id=conv_id)
    instruction = deduce_instruction(message)

    return instruction

def perform_instruction(instructions, params):
    pass

def deduce_instruction(self,message):
    threshold = 0.6
    message_embedding = MODEL.encode([message],normalize_embeddings=True)
    scores = util.cos_sim(message_embedding, example_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    if best_score >= threshold:
        return example_labels[best_idx]
    return "unknown"

def deduce_params(self,message):
    pass

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
        best_mood = mood_labels[best_idx]
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

