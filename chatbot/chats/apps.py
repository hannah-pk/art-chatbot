from django.apps import AppConfig


class ChatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chats'

    def ready(self):
        # Start a lightweight background thread to periodically cleanup anonymous conversations.
        # NOTE: This simple scheduler is intended for development or single-process deployments.
        # In production with multiple worker processes (gunicorn, uwsgi) this will run per worker.
        import threading
        import time
        import os
        from django.conf import settings
        import chats.signals

        # NEW LOGIC: Only skip if we are in the 'interactive' shell or managing migrations
        # This allows it to run under Gunicorn but not during 'python manage.py migrate'
        import sys
        if 'manage.py' in sys.argv and ('migrate' in sys.argv or 'makemigrations' in sys.argv):
            return

        try:
            from .cleanup import cleanup_anonymous_conversations,cleanup_user_image
        except Exception:
            return

        def _worker():
            while True:
                try:
                    cleanup_user_image(dry_run=False)
                    cleanup_anonymous_conversations(dry_run=False)
                except Exception:
                    pass
                time.sleep(60)  # 1 minute

        t = threading.Thread(target=_worker, daemon=True, name='conv-cleaner')
        t.start()
