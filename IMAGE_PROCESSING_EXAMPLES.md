# Image Processing Examples

This file contains practical examples for extending the image processing functionality.

## Basic Image Analysis

### Extract Image Dimensions and Color Mode
```python
def process_image_in_memory(image):
    """Extract basic image information"""
    image_data = {
        'width': image.width,
        'height': image.height,
        'size': image.size,
        'format': image.format,  # 'JPEG', 'PNG', etc.
        'mode': image.mode,       # 'RGB', 'RGBA', 'L', etc.
    }
    return image_data
```

## Advanced Image Analysis Examples

### Extract Dominant Color
```python
from PIL import Image
from collections import Counter

def get_dominant_color(image, num_colors=3):
    """Extract the most common colors from an image"""
    # Resize for faster processing
    image.thumbnail((100, 100))
    
    # Convert to RGB if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get all pixels
    pixels = list(image.getdata())
    
    # Count color frequency
    color_counts = Counter(pixels)
    most_common = color_counts.most_common(num_colors)
    
    return [
        {
            'color': rgb,
            'frequency': count,
            'hex': '#{:02x}{:02x}{:02x}'.format(*rgb)
        }
        for rgb, count in most_common
    ]

def process_image_in_memory(image):
    """Process image and extract color palette"""
    image_data = {
        'size': image.size,
        'format': image.format,
        'mode': image.mode,
        'dominant_colors': get_dominant_color(image)
    }
    return image_data
```

### Detect Brightness
```python
def get_image_brightness(image):
    """Calculate overall brightness of an image"""
    from PIL import ImageStat
    
    # Convert to grayscale
    bw = image.convert('L')
    stat = ImageStat.Stat(bw)
    brightness = stat.mean[0]  # 0-255 scale
    
    return {
        'brightness': brightness,
        'brightness_level': 'dark' if brightness < 85 else 'medium' if brightness < 170 else 'bright'
    }

def process_image_in_memory(image):
    image_data = {
        'size': image.size,
        'brightness': get_image_brightness(image)
    }
    return image_data
```

## Using Image Data in Request Processing

### Example: Incorporate Brightness into Mood Detection
```python
def process_request(message, conv, image_file=None):
    message_embedding = MODEL.encode([message], normalize_embeddings=True)
    
    if not Request.objects.filter(conversation=conv).exists():
        r = Request.objects.create(conversation=conv)
        instruction = deduce_instruction(message)
        if instruction is None:
            return clarifying_response()
        r.set_instruction(instruction)
        image_needed = deduce_image_needed(message_embedding, r)
        r.set_image_needed(image_needed)

    r = Request.objects.get(conversation=conv)
    mood = deduce_mood(message)
    r.add_params('mood', mood)
    
    # Process image if provided and needed
    if image_file and r.image_needed:
        try:
            img = Image.open(image_file)
            image_analysis = process_image_in_memory(img)
            
            # Enhance mood based on image brightness
            if image_analysis.get('brightness'):
                brightness_level = image_analysis['brightness']['brightness_level']
                if brightness_level == 'dark' and not mood:
                    mood = 'moody'  # Default dark images to moody
            
            r.add_params('image', image_analysis)
        except Exception as e:
            print(f"Error processing image: {e}")
            return "There was an error processing your image. Please try again."
    
    missing_params = r.missing_params()
    if missing_params is None:
        return perform_instruction(r.instruction, r.params)
    else:
        return clarify_params(missing_params)
```

## Edge Detection Example

```python
import numpy as np
from PIL import Image, ImageFilter

def detect_edges(image):
    """Detect edges in the image"""
    # Convert to grayscale
    gray = image.convert('L')
    
    # Apply edge detection
    edges = gray.filter(ImageFilter.FIND_EDGES)
    
    # Count edge pixels
    pixels = np.array(edges)
    edge_count = np.count_nonzero(pixels)
    edge_percentage = (edge_count / pixels.size) * 100
    
    return {
        'edge_percentage': round(edge_percentage, 2),
        'complexity': 'high' if edge_percentage > 20 else 'medium' if edge_percentage > 5 else 'low'
    }

def process_image_in_memory(image):
    image_data = {
        'size': image.size,
        'edge_detection': detect_edges(image)
    }
    return image_data
```

## Aspect Ratio Analysis

```python
def analyze_aspect_ratio(image):
    """Analyze image aspect ratio"""
    width, height = image.size
    aspect_ratio = width / height if height > 0 else 1
    
    if abs(aspect_ratio - 1) < 0.1:
        ratio_type = 'square'
    elif aspect_ratio > 1:
        ratio_type = 'landscape'
    else:
        ratio_type = 'portrait'
    
    return {
        'aspect_ratio': round(aspect_ratio, 2),
        'type': ratio_type,
        'ratio_text': f'{width}:{height}'
    }

def process_image_in_memory(image):
    image_data = {
        'size': image.size,
        'aspect_ratio': analyze_aspect_ratio(image)
    }
    return image_data
```

## Histogram Analysis

```python
from PIL import Image, ImageStat

def get_color_histogram(image):
    """Get distribution of colors"""
    stat = ImageStat.Stat(image)
    
    channels = {
        'red': round(stat.mean[0]) if len(stat.mean) > 0 else None,
        'green': round(stat.mean[1]) if len(stat.mean) > 1 else None,
        'blue': round(stat.mean[2]) if len(stat.mean) > 2 else None,
    }
    
    return channels

def process_image_in_memory(image):
    # Convert to RGB to ensure 3 channels
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    image_data = {
        'size': image.size,
        'color_histogram': get_color_histogram(image)
    }
    return image_data
```

## Integration with perform_instruction

### Example: Edit Image Based on Mood and Color Analysis
```python
def perform_instruction(instruction, params):
    """Execute the determined instruction"""
    
    if instruction == 'edit_image':
        image_data = params.get('image')
        mood = params.get('mood')
        
        if image_data:
            dominant_colors = image_data.get('dominant_colors', [])
            brightness = image_data.get('brightness', {})
            
            # Generate response based on analysis
            response = f"I can help you edit this image! "
            response += f"It's {brightness.get('brightness_level')} and has a {mood} mood. "
            
            if dominant_colors:
                hex_colors = [c['hex'] for c in dominant_colors[:2]]
                response += f"Main colors: {', '.join(hex_colors)}"
            
            return response
    
    # ... other instruction handling
    return "Processing..."
```

## Size and Format Validation

```python
def validate_image(image_file):
    """Validate image before processing"""
    try:
        img = Image.open(image_file)
        
        # Validate format
        if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
            return False, f"Unsupported format: {img.format}"
        
        # Validate size
        width, height = img.size
        if width > 4000 or height > 4000:
            return False, "Image too large (max 4000x4000)"
        
        if width < 100 or height < 100:
            return False, "Image too small (min 100x100)"
        
        return True, img
    except Exception as e:
        return False, str(e)

# In process_request():
if image_file and r.image_needed:
    is_valid, result = validate_image(image_file)
    if not is_valid:
        return f"Image validation failed: {result}"
    
    img = result
    image_analysis = process_image_in_memory(img)
    r.add_params('image', image_analysis)
```

## Using NumPy for Advanced Analysis

```python
import numpy as np
from PIL import Image

def analyze_image_complexity(image):
    """Calculate image complexity using standard deviation"""
    # Convert to numpy array
    arr = np.array(image.convert('L'))  # Convert to grayscale
    
    # Calculate standard deviation
    complexity = float(np.std(arr))
    
    return {
        'complexity_score': round(complexity, 2),
        'complexity_level': 'high' if complexity > 50 else 'medium' if complexity > 20 else 'low'
    }

def process_image_in_memory(image):
    image_data = {
        'size': image.size,
        'complexity': analyze_image_complexity(image)
    }
    return image_data
```

## Recommended Packages for Advanced Use

```bash
# Image processing and analysis
pip install Pillow              # Already needed
pip install numpy               # Numerical operations
pip install scikit-image        # Advanced image processing
pip install opencv-python       # Computer vision (alternative to PIL)

# Optional: ML-based analysis
pip install torch torchvision   # For deep learning models
pip install transformers        # For image classification
```

## Performance Tips

1. **Resize large images** before analysis to improve speed:
   ```python
   image.thumbnail((800, 800))
   ```

2. **Cache analysis results** if same image processed multiple times:
   ```python
   image_hash = hashlib.md5(image_data).hexdigest()
   ```

3. **Use grayscale** for basic analysis to reduce processing:
   ```python
   gray = image.convert('L')
   ```

4. **Set timeouts** for long-running analyses:
   ```python
   from django.db import connection
   connection.ensure_connection()  # Don't let connection drop
   ```

---

These examples provide a foundation for building sophisticated image analysis into your chatbot!
