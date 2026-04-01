from django.db.models.signals import pre_delete
from django.dispatch import receiver
from chats.models import Image, Message
import cloudinary.uploader as uploader

@receiver(pre_delete, sender=Image)
def delete_cloudinary_image(sender, instance, **kwargs):
    uploader.destroy(instance.public_id, type="authenticated", resource_type="image")

@receiver(pre_delete, sender=Message)
def delete_message_image(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete()  # triggers Image.delete() which cleans Cloudinary
