from sentence_transformers import SentenceTransformer, util
import torch
from nltk import pos_tag, word_tokenize
from chats.models import Request
import io
import numpy as np
import cv2 as cv
from sklearn.cluster import KMeans
#from nltk.corpus import stopwords
stop_words = ['colour']
import os
import uuid
from django.conf import settings

#stop_words = set(stopwords.words('english'))
KEEP_TAGS = {"JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS"}
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

example_data = torch.load('embeddings/intent.pt',weights_only=False)
example_labels = example_data['labels']
example_embeddings = example_data['embeddings']

mood_data = torch.load('embeddings/mood.pt',weights_only=False)
mood_labels = mood_data['labels']
mood_embeddings = mood_data['embeddings']

#image_param_data = torch.load('embeddings/image.pt',weights_only=False)
#image_param_embeddings = image_param_data['embeddings']
mood_colours = {
    'happy':(30,224,224),
    'calm':(60,96,224),
    'angry':(0,224,96),
    'sad':(120,96,96)
}

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
            return clarifying_response(), None
    r.set_instruction(instruction)
    
    if not r.needs_image:
        image_needed = deduce_image_needed(message_embedding, r)
        r.set_image_needed(image_needed)

    mood = deduce_mood(message)
    r.add_params('mood', mood)
    
    # Process image if provided and needed
    if image_file and r.needs_image:
        try:
            # image_file is already a path to the saved file
            r.add_params('image', image_file)
        except Exception as e:
            print(f"Error processing image: {e}")
            return "There was an error processing your image. Please try again."
    
    missing_params = r.missing_params()
    if missing_params is None:
        result = perform_instruction(r)
        # Normalize to a 2-tuple: (response, image_or_None)
        if isinstance(result, (list, tuple)):
            if len(result) >= 2:
                return result[0], result[1]
            if len(result) == 1:
                return result[0], None
        return result, None
    else:
        return clarify_params(missing_params), None



def perform_instruction(request):
    instruction = request.instruction
    params = request.params
    request.delete()
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

def deduce_image_needed(message,request):
    if request.instruction == "edit_image":
        return True
    #threshold = 0.6
    image_needed = False
    #img_scores = util.cos_sim(msg_embedding,image_param_embeddings)[0]
    #best_idx = img_scores.argmax().item()
    #best_score = img_scores[best_idx].item()

    #if best_score >= threshold:
        #image_needed = True
    if 'this' in message:
        return True
    return image_needed


def deduce_mood(message):
    threshold = 0.5
    filtered_message = filter_common_words(extract_relevant_words(message))
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

def sample_hues(mean,n):
    hue = np.random.normal(mean,45,n)
    for i in range(len(hue)):
        hue[i] = int(hue[i]%180)
    return hue

def sample_saturation_or_value(mean,n):
    s_or_v = np.random.normal(mean,30,n)
    for i in range(len(s_or_v)):
        x = s_or_v[i]
        if x > 255:
            s_or_v[i] = 255
        if x < 0:
            s_or_v[i] = 0
        s_or_v[i] = int(s_or_v[i])
    return s_or_v

def sample_colours(mood,n):
    hue_mean, saturation_mean,value_mean = mood_colours[mood]
    hues = sample_hues(hue_mean,n)
    saturations = sample_saturation_or_value(saturation_mean,n)
    values = sample_saturation_or_value(value_mean,n)
    return np.stack((hues,saturations,values),axis=1)

def generate_colour_palette_image(colours):
    img_height=500
    img_width=300
    row_height = img_height//len(colours)

    result = np.zeros((row_height * len(colours), img_width, 3), dtype=colours.dtype)

    for i, colour in enumerate(colours):
        result[i*row_height:(i+1)*row_height, :, :] = colour
    return result

def darken_colour(colour,grade=1):
    hue,saturation,value = colour
    if grade==2:
        hue += 90
    else:
        if hue<=30 or hue >150: #if colour between blue to yellow (including magenta, red)
            hue -= 15
        else: #if colour between yellow and blue (including green, cyan)
            hue += 15
    hue = hue%180
    change_scale = 10*grade
    saturation = min(255,saturation+change_scale)
    value = max(0,value-change_scale)
    return (hue,saturation,value)

def lighten_colour(colour,grade=1):
    hue,saturation,value = colour
    if grade==2:
        hue += 90
    else:
        if hue<30 or hue >=150: #if colour between blue to yellow (including magenta, red)
            hue += 15
        else: #if colour between yellow and blue (including green, cyan)
            hue -= 15
    hue = hue%180
    change_scale = 10*grade
    saturation = max(0,saturation-change_scale)
    value = min(255,value+change_scale)
    return (hue,saturation,value)

def soft_light_filter(colour,mood):
    #based off the official soft light filter in image editing apps such as Photoshop
    mood_colour = mood_colours[mood]
    if mood_colour[2] <= 128:
        intermed = np.subtract(colour,np.multiply(colour,colour))
    else:
        intermed = np.subtract(np.sqrt(colour),colour)
    result = np.add(
        np.multiply(
            np.subtract(np.multiply(2,mood_colour),(180,255,255)),
            intermed),
        colour
    )
    return result

def colour_palette(mood, image=None, number=5):
    n = number*4
    colours = []
    if image is not None:
        img = cv.imread(image)
        converted_image = cv.cvtColor(img,cv.COLOR_BGR2HSV) #in artistic contexts, hsv or hsl are more commonly used for colouring
        unique_values = np.unique(converted_image.reshape(-1,3),axis=0)
        n = n//2
        for i in range(n):
            colours.append(np.random.choice(unique_values))
    mood_based_colours = sample_colours(mood,n)
    for c in mood_based_colours:
        colours.append(c)
    kmeans = KMeans(n_clusters=number).fit(colours)
    result_img = generate_colour_palette_image(kmeans.cluster_centers_)


    # write the generated numpy image to a temporary file and return its path
    try:
        out_img = result_img
        if out_img.dtype != np.uint8:
            out_img = np.clip(out_img, 0, 255).astype(np.uint8)
        # convert RGB -> BGR for OpenCV
        bgr = cv.cvtColor(out_img, cv.COLOR_HSV2BGR)

        media_dir = getattr(settings, 'MEDIA_ROOT', None)
        if not media_dir:
            media_dir = os.path.join(os.getcwd(), 'media')
        temp_dir = os.path.join(media_dir, 'temp_images')
        os.makedirs(temp_dir, exist_ok=True)
        filename = f"palette_{uuid.uuid4().hex}.png"
        save_path = os.path.join(temp_dir, filename)

        cv.imwrite(save_path, bgr)
        return f'colour_palette {mood} {number}', save_path
    except Exception as e:
        print(f"Failed to write palette image: {e}")
        return f'colour_palette {mood} {number}', None

def edit_image(image, mood):
    if image is not None:
        img = cv.imread(image)
        converted_image = cv.cvtColor(img,cv.COLOR_BGR2HSV)
    vectorise_soft_light = np.vectorize(soft_light_filter)
    filtered_img = vectorise_soft_light(converted_image)
    return 'edit_image' + mood, image

