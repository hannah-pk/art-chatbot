from sentence_transformers import SentenceTransformer, util
import torch
from nltk import pos_tag, word_tokenize
from chats.models import Request
from PIL import Image
import io
import numpy as np
#from nltk.corpus import stopwords

#stop_words = set(stopwords.words('english'))
KEEP_TAGS = {"JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS"}
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

example_data = torch.load('embeddings/intent.pt',weights_only=False)
example_labels = example_data['labels']
example_embeddings = example_data['embeddings']

mood_data = torch.load('embeddings/mood.pt',weights_only=False)
mood_labels = mood_data['labels']
mood_embeddings = mood_data['embeddings']

image_param_data = torch.load('embeddings/image.pt',weights_only=False)
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

def clarifying_response():
    return "Sorry, I'm entirely sure what you are trying to ask for. Please could you rephrase your request in a way that I might understand?"

def clarify_params(param):
    if param == 'mood':
        return "Could you give further detail on the kind of mood or atmosphere you're hoping to achieve?"
    elif param == 'image':
        return "It seems I'm missing an image. Could you please provide the image?"


def process_request(message, conv, image_file=None):
    """
    Process user request with optional image data.
    Image data is processed in-memory and not stored long-term.
    
    Args:
        message: Text message from user
        conv: Conversation object
        image_file: Optional uploaded image file (InMemoryUploadedFile or similar)
    
    Returns:
        Response string from the chatbot
    """
    message_embedding = MODEL.encode([message], normalize_embeddings=True)
    
    r = Request.objects.get_or_create(conversation=conv)[0]
    instruction= r.instruction
    if instruction is None:
        instruction = deduce_instruction(message)
        if instruction is None: #if instruction is still None after trying to deduce the instruction
            return clarifying_response()
    r.set_instruction(instruction)
    image_needed = deduce_image_needed(message_embedding, r)
    r.set_image_needed(image_needed)

    mood = deduce_mood(message)
    r.add_params('mood', mood)
    
    # Process image if provided and needed
    if image_file and r.image_needed:
        try:
            # Load image from uploaded file into memory
            img = Image.open(image_file)
            # You can process the image here without saving it
            # For example: analyze it, extract features, etc.
            r.add_params('image', np.array(img))
        except Exception as e:
            print(f"Error processing image: {e}")
            return "There was an error processing your image. Please try again."
    
    missing_params = r.missing_params()
    if missing_params is None:
        return perform_instruction(r.instruction, r.params)
    else:
        return clarify_params(missing_params)



def perform_instruction(instruction, params):
    if instruction=="edit_image":
        return edit_image(**params)
    elif instruction=="colour_palette":
        return colour_palette(**params)
    else:
        return instruction

def deduce_instruction(message):
    threshold = 0.6
    message_embedding = MODEL.encode([message],normalize_embeddings=True)
    scores = util.cos_sim(message_embedding, example_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    if best_score >= threshold:
        return example_labels[best_idx]
    return None

def deduce_image_needed(msg_embedding,request):
    if request.instruction == "edit_image":
        return True
    threshold = 0.6
    image_needed = False
    img_scores = util.cos_sim(msg_embedding,image_param_embeddings)[0]
    best_idx = img_scores.argmax().item()
    best_score = img_scores[best_idx].item()

    if best_score >= threshold:
        image_needed = True
    return image_needed


def deduce_mood(message):
    threshold = 0.5
    filtered_message = extract_relevant_words(message)
    print(filtered_message)
    words = filtered_message.split()
    mood = None
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

def colour_palette(mood,image=None,number=5):
    i = ""
    if image is not None:
        i = " image "
    return 'colour_palette '+ mood + i + str(number)

def edit_image(image,mood):
    i = ""
    if image is not None:
        i = " image "
    return 'edit_image' + i + mood

