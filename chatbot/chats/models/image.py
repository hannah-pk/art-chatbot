from django.db import models
from cloudinary.models import CloudinaryField
import cloudinary.uploader as uploader
from django.core.validators import MaxLengthValidator, MinLengthValidator

class Image(models.Model):
    """
    Representation of an image that is part of a message.
    Contains the Cloudinary URL of the image and its public id, which will be useful when eventually deleting the image to maintain user privacy
    """
    public_id = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])
