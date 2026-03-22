from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Message

@receiver(post_delete, sender=Message)
def delete_image_on_message_delete(sender, instance, **kwargs):
    if instance.image:
        instance.image.delete(save=False)