from django.core.management.base import BaseCommand
from chats.cleanup import cleanup_anonymous_conversations,cleanup_user_image  
import time

class Command(BaseCommand):
    help = 'Cleans up expired conversations and images'

    def handle(self, *args, **options):
        retries = 3
        while retries > 0:
            try:
                # Your existing logic
                cleanup_user_image()
                cleanup_anonymous_conversations()
                break 
            except Exception as e:
                if "Control plane" in str(e):
                    self.stdout.write("Neon Control Plane busy, retrying...")
                    time.sleep(5)
                    retries -= 1
                else:
                    raise e
        
