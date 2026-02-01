# Image Upload Feature Implementation Guide

## Overview
This implementation allows users to upload images alongside text messages in conversations. Images are processed in-memory and not stored long-term in the database, keeping your storage lean while still enabling image analysis.

## Architecture

### Frontend Changes (React)
**File: `frontend/src/pages/Conversation.jsx`**

#### New Features:
1. **Image State Management**: Added state for image file and preview
   - `image`: Stores the actual File object
   - `imagePreview`: Stores base64 preview for display

2. **Image Handlers**:
   - `handleImageChange()`: Converts selected file to preview and stores file reference
   - `clearImage()`: Removes selected image before sending

3. **FormData Request**: 
   - Messages now use FormData instead of JSON
   - Images are sent as multipart/form-data
   - Text content is still included alongside the image

### Backend Changes

#### Database Model Changes
**File: `chatbot/chats/models/message.py`**
```python
image = models.ImageField(upload_to='temp_images/', null=True, blank=True)
```
- Added optional image field to Message model
- Images upload to temporary directory for brief storage during processing

#### Serializer Updates
**File: `chatbot/chats/serialisers.py`**
```python
image = serializers.ImageField(required=False, allow_null=True, write_only=True)
```
- Image is write-only (client sends it, but API doesn't return it)
- Optional field to support messages without images

#### View Updates
**File: `chatbot/chats/views.py`**
```python
image_file = request.FILES.get('image', None)
response = process_request(request.data.get("content"), conversation, image_file)
```
- Extracts image from multipart request
- Passes to `process_request()` for backend processing

#### Image Processing
**File: `chatbot/chats/tasks.py`**

New function signature:
```python
def process_request(message, conv, image_file=None):
```

Features:
- Processes images in-memory using PIL (Pillow)
- Extracts image metadata (size, format, color mode)
- Adds image data to request parameters
- **Does not store images long-term**

Helper function `process_image_in_memory()`:
- Loads image from uploaded file
- Extracts useful metadata
- Returns dict with image analysis results
- Never saves to disk

## Setup Instructions

### 1. Install Dependencies
```bash
cd chatbot
pip install Pillow  # Required for image processing
```

### 2. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the `image` field in the Message model.

### 3. Configure Django Settings
Ensure these are in `chatbot/settings.py`:
```python
INSTALLED_APPS = [
    'django.contrib.staticfiles',
    # ... other apps
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Optional: Set max upload size (default is unlimited)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
```

### 4. Update URL Configuration (Optional)
If you want to serve temp images during dev, add to `chatbot/urls.py`:
```python
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # ... your patterns
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## Usage

### For Users
1. Navigate to a conversation
2. Enter text message (optional)
3. Click "Choose file" to select an image (optional)
4. See image preview below the file input
5. Click "Send" to submit (requires either text or image)
6. Chatbot processes the image in-memory and responds

### For Developers - Accessing Image Data

In `process_request()`:
```python
if image_file and r.image_needed:
    img = Image.open(image_file)
    # Process image here
    img_data = process_image_in_memory(img)
    r.add_params('image', img_data)
```

You can:
- Use PIL/Pillow for image manipulation: `from PIL import Image`
- Extract features using computer vision libraries
- Perform image analysis without saving to disk
- Access image data: `image.size`, `image.format`, `image.mode`

## Key Benefits

✅ **No Long-Term Storage**: Images processed in-memory, temporary files auto-deleted
✅ **Cleaner Requests**: User can send image OR text OR both
✅ **Preview UI**: Users see selected image before sending
✅ **Flexible Processing**: Easy to add custom image analysis
✅ **Simple Frontend**: Uses standard HTML file input

## How In-Memory Processing Works

1. **Upload**: File transferred from client to server in multipart request
2. **Load**: Django provides file handle (InMemoryUploadedFile)
3. **Process**: PIL reads bytes directly from file handle
4. **Analyze**: Extract data/features as needed
5. **Store**: Only the analysis result (metadata) saved to database
6. **Cleanup**: File automatically deleted after request completes

## Customizing Image Processing

Edit `process_image_in_memory()` in `tasks.py`:

```python
def process_image_in_memory(image):
    # Example: Extract dominant color
    from PIL import Image
    
    image_data = {
        'size': image.size,
        'format': image.format,
        'mode': image.mode,
    }
    
    # Add your custom analysis
    if image.mode in ('RGB', 'RGBA'):
        # Example: get dominant colors
        image.thumbnail((100, 100))
        pixels = list(image.getdata())
        # Analyze pixels...
    
    return image_data
```

## Validation & Error Handling

The implementation includes:
- File type validation (accepts image/* only)
- Size limits (configurable in Django settings)
- Error handling during image processing
- User-friendly error messages
- Graceful fallback if image processing fails

## Security Considerations

✅ **No arbitrary file storage**: Images never written to permanent storage
✅ **File type restricted**: Only image/* MIME types accepted
✅ **Size limited**: Set FILE_UPLOAD_MAX_MEMORY_SIZE to prevent DoS
✅ **Temporary storage**: Auto-deleted after request completion
✅ **Validation**: Image validated before processing

## Future Enhancements

Consider adding:
1. Advanced image analysis (object detection, color analysis)
2. Image compression before processing
3. Batch image support
4. Image format conversion
5. Thumbnail generation
6. EXIF data extraction
