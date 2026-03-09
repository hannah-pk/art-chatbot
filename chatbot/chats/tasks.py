from sentence_transformers import SentenceTransformer, util
import torch
from nltk import pos_tag, word_tokenize
from chats.models import Request
import io
import numpy as np
import cv2 as cv
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances
#from nltk.corpus import stopwords
stop_words = ['colour']
import os
import uuid
from django.conf import settings
import spacy
nlp = spacy.load("en_core_web_sm")

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
    'happy':(30,255,190),
    'calm':(60,64,190),
    'angry':(0,190,64),
    'sad':(100,190,64)
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

def split_text(msg):
    doc = nlp(msg)
    # Find the root verb, split after its direct object or complement
    for token in doc:
        if token.dep_ in ("acomp", "advmod", "prep") and token.i > 0:
            split_point = token.idx
            return msg[:split_point].strip(), msg[split_point:].strip()
    return msg, ""

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
    instruction_half,mood_half = split_text(message)
    print(instruction_half+"::"+mood_half)
    instruction_embedding = MODEL.encode([instruction_half], normalize_embeddings=True)
    
    r = Request.objects.get_or_create(conversation=conv)[0]

    # Process image if provided, even if not necessarily needed
    if image_file:
        try:
            # image_file is already a path to the saved file
            r.add_params('image', image_file)
        except Exception as e:
            print(f"Error processing image: {e}")
            return "There was an error processing your image. Please try again."

    instruction= r.instruction
    if instruction is None:
        instruction = deduce_instruction(message)
        if instruction is None: #if instruction is still None after trying to deduce the instruction
            return clarifying_response(), None
    r.set_instruction(instruction)
    
    if not r.needs_image:
        image_needed = deduce_image_needed(instruction_embedding, r)
        r.set_image_needed(image_needed)

    params = r.params
    if params.get("mood") is None:
        mood = deduce_mood(message)
        r.add_params('mood', mood)
    

    
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
    hue = np.random.normal(mean,30,n)
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

def colour_contrast(bgr,hsv):
    num_grades = 5 #5 grades of shading
    kmeans = KMeans(n_clusters=num_grades).fit(bgr)
    centres = kmeans.cluster_centers_
    labels = kmeans.labels_
    #rearrange the labels to be in ascending order of centre value
    order = np.argsort(centres[:,0])
    sorted_labels = np.argsort(order)[labels]
    for i in range(len(labels)):
        grade = sorted_labels[i]
        #hsv[i] = (0,0,50*grade)
        if grade < 2:
            n = 2-grade
            hsv[i] = darken_colour(hsv[i],n)
        elif grade > 2:
            n = grade-2
            hsv[i] = lighten_colour(hsv[i],n)
    return hsv


def darken_colour(colour,grade=1):
    hue,saturation,value = colour
    if grade==2:
        if hue >=90:
            hue -= 90
        else:
            hue += 90
    else:
        if hue<=30 or hue >150: #if colour between blue to yellow (including magenta, red)
            hue = (hue-15)%180
        else: #if colour between yellow and blue (including green, cyan)
            hue += 15
    change_scale = 20*grade
    saturation = min(255,saturation+change_scale)
    value = max(0,value-change_scale)
    return (hue,saturation,value)

def lighten_colour(colour,grade=1):
    hue,saturation,value = colour
    if grade==2:
        if hue >=90:
            hue -= 90
        else:
            hue += 90
    else:
        if hue<30 or hue >=150: #if colour between blue to yellow (including magenta, red)
            hue += 15
        else: #if colour between yellow and blue (including green, cyan)
            hue = (hue-15)%180
    change_scale = 20*grade
    saturation = max(0,saturation-change_scale)
    value = min(255,value+change_scale)
    return (hue,saturation,value)

def soft_light_filter(bgr_img,mood):
    #based off the official soft light filter in image editing apps such as Photoshop
    B=bgr_img.astype(np.float32)/255
    F = (cv.cvtColor(np.array([[mood_colours[mood]]],dtype=np.uint8),cv.COLOR_HSV2BGR)/255)[0][0]

    
    R = np.where(F <= 0.5,
                 B - (1 - 2*F) * B * (1 - B),
                 B + (2*F - 1) * (np.sqrt(B) - B))
    
    # Convert back to 0-255
    return np.clip(R * 255, 0, 255).astype(np.uint8)


def colour_palette(mood, image=None, number=5):
    n = number*4
    colours = []
    if image is not None:
        img = cv.imread(image)
        #converted_image = cv.cvtColor(img,cv.COLOR_BGR2HSV) #in artistic contexts, hsv or hsl are more commonly used for colouring
        unique_values = np.unique(img.reshape(-1,3),axis=0)
        n = n//2
        for i in range(n):
            colours.append(unique_values[np.random.randint(0,len(unique_values))])
    mood_based_colours = sample_colours(mood,n)
    for c in mood_based_colours:
        colours.append(c)
    kmeans = KMeans(n_clusters=number).fit(colours)
    result_img = generate_colour_palette_image(kmeans.cluster_centers_).astype(np.uint8)
    bgr = cv.cvtColor(result_img, cv.COLOR_HSV2BGR)
    return f'colour_palette {mood} {number}', save_img(bgr)

def edit_image(image, mood):
    if image is not None:
        img = cv.imread(image)
    hsv =cv.cvtColor(img,cv.COLOR_BGR2HSV)
    h, w, _ = img.shape
    #reshaped_bgr = img.reshape(-1, 3)
    #reshaped_hsv = hsv.reshape(-1, 3)
    #processed = soft_light_filter(img,mood)
    processed = img
    #processed = soft_light_filter(processed,mood)
    reshaped_bgr = processed.reshape(-1, 3)
    reshaped_hsv = processed.reshape(-1,3)

    processed = colour_contrast(reshaped_bgr,reshaped_hsv)
    processed = soft_light_filter(processed,mood)
    final = processed.reshape(h,w,3)
    #final = cv.cvtColor(final,cv.COLOR_HSV2BGR)
    #final = soft_light_filter(final,mood)

    #processed = np.array([
    #    soft_light_filter(pixel, mood)
    #    for pixel in reshaped
    #], dtype=converted_image.dtype)
    return 'edit_image' + mood, save_img(final)

def save_img(pixels):
    # write the generated numpy image to a temporary file and return its path
    try:
        """ out_img = pixels
        if out_img.dtype != np.uint8:
            out_img = np.clip(out_img, 0, 255).astype(np.uint8)
        # convert HSV -> BGR for OpenCV
        bgr = cv.cvtColor(out_img, cv.COLOR_HSV2BGR) """

        media_dir = getattr(settings, 'MEDIA_ROOT', None)
        if not media_dir:
            media_dir = os.path.join(os.getcwd(), 'media')
        temp_dir = os.path.join(media_dir, 'temp_images')
        os.makedirs(temp_dir, exist_ok=True)
        filename = f"image_{uuid.uuid4().hex}.png"
        save_path = os.path.join(temp_dir, filename)

        cv.imwrite(save_path, pixels)
        return save_path
    except Exception as e:
        print(f"Failed to write image: {e}")
        return None