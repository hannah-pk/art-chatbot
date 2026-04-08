from django.core.management.base import BaseCommand
from chats.cleanup import cleanup_anonymous_conversations,cleanup_user_image  


class Command(BaseCommand):
    help = 'Cleans up expired conversations and images'

    def handle(self, *args, **options):
        cleanup_user_image()
        cleanup_anonymous_conversations()
