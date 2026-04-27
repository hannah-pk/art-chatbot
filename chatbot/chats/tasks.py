# import psutil,os
# process = psutil.Process(os.getpid())
# print(f"Baseline: {process.memory_info().rss / 1024 / 1024:.1f} MB")

from chats.models import Request,Image
import numpy as np
import cv2 as cv
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity as cos_sim
from .helpers import get_embeddings,read_json, get_signed_url
import urllib.request
import uuid

# print(f"Baseline: {process.memory_info().rss / 1024 / 1024:.1f} MB")

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ONNX_MODEL_PATH = str(BASE_DIR / 'onnx_model')

stop_words = ['colour']
KEEP_TAGS = {"JJ", "JJR", "JJS", "NN", "NNS", "NNP", "NNPS"}

example_labels, example_embeddings = get_embeddings('embeddings/intent.pt')
mood_labels, mood_embeddings = get_embeddings('embeddings/mood.pt')

mood_colours = read_json('mappings/mood_colour_mappings.json')

tokenizer = None
model = None
nlp = None

# print(f"Baseline: {process.memory_info().rss / 1024 / 1024:.1f} MB")

def get_tokenizer():
    global tokenizer
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(ONNX_MODEL_PATH)
    return tokenizer

def get_model():
    global model
    if model is None:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        model = ORTModelForFeatureExtraction.from_pretrained(ONNX_MODEL_PATH)
    return model

def get_nlp():
    global nlp
    if nlp is None:
        import spacy
        nlp = spacy.load("en_core_web_sm")
    return nlp

def encode(texts, normalize=True):
    inputs = get_tokenizer()(texts, return_tensors='np', padding=True, truncation=True)
    outputs = get_model()(**inputs)
    embeddings = outputs.last_hidden_state.mean(axis=1)
    if normalize:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms
    return embeddings

def filter_common_words(text):
    words = text.lower().split()
    filtered_words = [word for word in words if word.lower() not in stop_words]
    return ' '.join(filtered_words)

def extract_relevant_words(text):
    doc = get_nlp()(text)
    relevant_words = [token.text for token in doc if token.pos_ in {"ADJ", "NOUN", "PROPN"}]
    return ' '.join(relevant_words)

def final_response():
    return "Here you go!"

def clarifying_response():
    return "Sorry, I'm not entirely sure what you are trying to ask for. Please could you rephrase your request in a way that I might understand?"

def clarify_params(param):
    if param == 'mood':
        return "Could you give further detail on the kind of mood or atmosphere you're hoping to achieve?"
    elif param == 'image':
        return "It seems I'm missing an image. Could you please provide the image?"

def split_text(msg):
    doc = get_nlp()(msg)
    # Find the root verb, split after its direct object or complement
    for token in doc:
        if token.dep_ in ("acomp", "advmod", "prep") and token.i > 0:
            split_point = token.idx
            return msg[:split_point].strip(), msg[split_point:].strip()
    return msg, ""

def process_request(message):
    """
    Process user request with optional image data.
    Image data is processed in-memory and not stored long-term.
    
    Args:
        message: Message from user (including text content and image)
    
    Returns:
        Response string from the chatbot
    """
    conversation = message.conversation
    r = Request.objects.get_or_create(conversation=conversation)[0]
    # Process image if provided, even if not necessarily needed
    image = message.image
    if image:
        try:
            # get a secure Cloudinary url for the image
            url = get_signed_url(image)
            r.add_params('image', url)
        except Exception as e:
            print(f"Error processing image: {e}")
            return "There was an error processing your image. Please try again.", None

    text = message.content
    # get the instruction that the user wants to be performed (only if there is text to be analysed)
    if text:
        instruction_half,_ = split_text(text)
        #instruction can be overwritten at any time
        instruction = deduce_instruction(instruction_half)
        if instruction is not None:
            r.set_instruction(instruction)
        
        # detect from the message content whether the instruction should require an image
        # once it detects an image is needed, that requirement cannot disappear
        if not r.get_image_needed():
            image_needed = deduce_image_needed(text, r)
            r.set_image_needed(image_needed)

        # detect the parameters that will be needed for the successful execution of the instruction
        params = r.get_params()
        if params.get("mood") is None:
            mood = deduce_mood(text)
            r.add_params('mood', mood)
    
    #if the current ongoing request has no instruction, ask for further clarification
    if r.get_instruction() is None:
        return clarifying_response(), None
    
    # check if the request contains enough parameters to successfully perform the instruction
    # if there are enough, perform the instruction, otherwise ask for further clarification
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
    """
    Performs the instruction contained within the passed-in request parameter, passing in the parameters contained within the request instance
    """
    instruction = request.instruction
    params = request.params
    request.delete()
    if instruction=="edit_image":
        result = edit_image(**params)
        return result
    elif instruction=="colour_palette":
        result = colour_palette(**params)
        return result
    else:
        return instruction

def deduce_instruction(message):
    """
    Uses cosine similarity to prompt example embeddings to deduce the instruction.
    Compares entire given message.

    Returns either "edit_image","colour_palette" or None (in the case where the first two have not been deduced with enough certainty)
    """
    threshold = 0.6
    message_embedding = encode([message],normalize=True)
    scores = cos_sim(message_embedding, example_embeddings)[0]
    best_idx = scores.argmax().item()
    best_score = scores[best_idx].item()

    if best_score >= threshold:
        return example_labels[best_idx]
    return None 

def deduce_image_needed(message,request):
    """
    Looks at keywords to identify whether an image is required for the user's request to be successfully executed

    Returns a boolean value
    """
    if request.instruction == "edit_image":
        return True
    image_needed = False
    #the current check is very simplistic, may need to refine for future work
    if 'this' in message:
        return True
    return image_needed


def deduce_mood(message):
    """
    Uses cosine similarity to mood synonym embeddings to deduce the mood the user wants to achieve
    Compares the individual words from a filtered version of the given message.

    Returns "happy", "calm", "angry", "sad" or None (in the case that none of the others were identified with enough certainty)
    """
    threshold = 0.5
    filtered_message = filter_common_words(extract_relevant_words(message))
    words = filtered_message.split()
    mood = None
    highscore = 0
    for word in words:
        word_embedding = encode([word],normalize=True)
        word_scores = cos_sim(word_embedding, mood_embeddings)[0]
        best_idx = word_scores.argmax().item()
        best_score = word_scores[best_idx].item()
        best_mood = mood_labels[best_idx]
        if best_score >= max(threshold,highscore):
            mood = best_mood
            highscore = best_score
    return mood

def sample_hues(mean,n):
    """
    Samples a random hue from a normal distribution, cycling around the range 0-180
    """
    hue = np.random.normal(mean,30,n)
    for i in range(len(hue)):
        hue[i] = int(hue[i]%180)
    return hue

def sample_saturation_or_value(mean,n):
    """
    Samples a saturation or value from a normal distribution, clipped between 0 and 255
    """
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
    """
    Samples n colours that are picked based on the colour associated with the given mood parameter
    """
    hue_mean, saturation_mean,value_mean = mood_colours[mood]
    hues = sample_hues(hue_mean,n)
    saturations = sample_saturation_or_value(saturation_mean,n)
    values = sample_saturation_or_value(value_mean,n)
    return np.stack((hues,saturations,values),axis=1)

def generate_colour_palette_image(colours):
    """
    Given a list of colours, produces a numpy array that can represent the colours as thick coloured strips in an image
    """
    img_height=500
    img_width=300
    row_height = img_height//len(colours)

    #initialise image array
    result = np.zeros((row_height * len(colours), img_width, 3), dtype=colours.dtype)

    #assign colours to bars in array
    for i, colour in enumerate(colours):
        result[i*row_height:(i+1)*row_height, :, :] = colour
    return result

def colour_contrast(bgr,hsv):
    """
    Uses colour theory to use all the digital parameters of a colour to increase the contrast
    HSV (hue, saturation, value) is a colour format commonly used in artistic contexts, hence is used in this function
    """
    num_grades = 5 #5 grades of shading
    merge_threshold = 20

    #kmeans clustering of the image pixel values
    kmeans = KMeans(n_clusters=num_grades).fit(bgr)
    centres = kmeans.cluster_centers_
    labels = kmeans.labels_

    #rearrange the labels to be in ascending order of centre value
    sorted_clusters = np.sort(centres)
    order = np.argsort(centres[:,0])
    sorted_labels = np.argsort(order)[labels]

    #merge the most extreme clusters with their neighbouring clusters if the centres are close enough
    dark_distance = np.linalg.norm(abs(sorted_clusters[0]-sorted_clusters[1]))
    if dark_distance < merge_threshold:
        sorted_labels[sorted_labels==0]=1
    light_distance = np.linalg.norm(abs(sorted_clusters[3]-sorted_clusters[4]))
    if light_distance < merge_threshold:
        sorted_labels[sorted_labels==4]=3

    #implement the actual colour contrasting
    for i in range(len(labels)):
        grade = sorted_labels[i]
        if grade < 2:
            n = 2-grade
            hsv[i] = darken_colour(hsv[i],n)
        elif grade > 2:
            n = grade-2
            hsv[i] = lighten_colour(hsv[i],n)
    return hsv


def darken_colour(colour,grade=1):
    """
    Darkens a pixel by shifting its hue, saturation and brightness, using colour theory
    """
    hue,saturation,value = colour
    if grade==2:
        if hue >=90:
            hue -= 90
        else:
            hue += 90
    else:
        if hue<=30 or hue >150: #shift down if colour between blue to yellow (including magenta, red)
            hue = (hue-15+180)%180
        else: #shift up if colour between yellow and blue (including green, cyan)
            hue += 15
    change_scale = 20*grade
    saturation = min(255,saturation+change_scale)
    value = max(0,value-change_scale)
    return (hue,saturation,value)

def lighten_colour(colour,grade=1):
    """
    Lightens a pixel by shifting its hue, saturation and brightness, using colour theory
    """
    hue,saturation,value = colour
    if grade==2: #brightest shade gets turned into complementary hue
        if hue >=90:
            hue -= 90
        else:
            hue += 90
    else:
        if hue<30 or hue >=150: #hue shifted up slightly if colour between blue to yellow (including magenta, red)
            hue += 15
        else: #hue shifted down slightly if colour between yellow and blue (including green, cyan)
            hue = (hue-15)%180
    change_scale = 20*grade
    saturation = max(0,saturation-change_scale) #decrease saturation
    value = min(255,value+change_scale) #increase brightness
    return (hue,saturation,value)

def soft_light_filter(bgr_img,mood):
    """
    Puts the provided image through a soft light filter 
    Based off the official soft light filter in image editing apps such as Photoshop
    Base layer (B) = bgr_img
    Blend layer (A) = mood
    Calculation: 
    A<=0.5: C=(2*A-1)*(B-B*B)+B
    A>0.5: C= (2*A-1)*(SQRT (B)-B) +B
    """
    #based off the official soft light filter in image editing apps such as Photoshop
    B=bgr_img.astype(np.float32)/255
    F = (cv.cvtColor(np.array([[mood_colours[mood]]],dtype=np.uint8),cv.COLOR_HSV2BGR)/255)[0][0]

    
    R = np.where(F <= 0.5,
                 B - (1 - 2*F) * B * (1 - B),
                 B + (2*F - 1) * (np.sqrt(B) - B))
    
    # Convert back to 0-255
    return np.clip(R * 255, 0, 255).astype(np.uint8)


def colour_palette(mood, image=None, number=5):
    """
    Generate a colour palette based on the implied mood from the user (and an image if it's provided)
    """
    n = number*4
    colours = []
    if image is not None:
        img = read_img(image)
        unique_values = np.unique(img.reshape(-1,3),axis=0)
        n = n//2
        for _ in range(n):
            colours.append(unique_values[np.random.randint(0,len(unique_values))])
    mood_based_colours = sample_colours(mood,n)
    for c in mood_based_colours:
        colours.append(c)
    kmeans = KMeans(n_clusters=number).fit(colours)
    result_img = generate_colour_palette_image(kmeans.cluster_centers_).astype(np.uint8)
    bgr = cv.cvtColor(result_img, cv.COLOR_HSV2BGR)
    return final_response(), save_img(bgr)

def edit_image(image, mood):
    """
    Edits the provided image according to the implied mood from the user.
    """
    img = read_img(image)
    h, w, _ = img.shape
    processed = img
    reshaped_bgr = processed.reshape(-1, 3)
    processed = soft_light_filter(reshaped_bgr,mood)
    hsv =cv.cvtColor(processed.reshape(h,w,3),cv.COLOR_BGR2HSV).reshape(-1,3)
    processed = colour_contrast(processed,hsv)
    final = processed.reshape(h,w,3)
    final = cv.cvtColor(final,cv.COLOR_HSV2BGR)
    return final_response(), save_img(final)

def read_img(url):
    """
    Takes an Image instance and returns the image array from the url (accessed through image.url)
    """
    response = urllib.request.urlopen(url)
    arr = np.asarray(bytearray(response.read()),dtype=np.uint8)
    img = cv.imdecode(arr,cv.IMREAD_COLOR)
    return img

def save_img(pixels):
    """
    Takes a numpy array, uploads it to Cloudinary and creates (and returns) Image instance for the image
    """
    # write the generated numpy image to a temporary file and return its path
    try:
        import cloudinary.uploader as uploader
        filename = f"image_{uuid.uuid4().hex}"
        success, buffer = cv.imencode(".png",pixels)
        if not success:
            raise ValueError("Failed to encode image.")
        result = uploader.upload(
            buffer.tobytes(),
            public_id = filename,
            type="authenticated",
            resource_type="image"
        )
        image_field = Image.objects.create(
            public_id = result["public_id"]
        )
        return image_field
    except Exception as e:
        print(f"Failed to write image: {e}")
        return None