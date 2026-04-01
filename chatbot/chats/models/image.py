from django.db import models
from cloudinary.models import CloudinaryField
import cloudinary.uploader as uploader
from django.core.validators import MaxLengthValidator, MinLengthValidator

class Image(models.Model):
    url = CloudinaryField('image', null=True, blank=True)
    public_id = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])

    def delete(self):
        uploader.destroy(self.public_id, type="authenticated",resource_type="image")
        super().delete()