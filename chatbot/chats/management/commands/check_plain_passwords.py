from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Check for user accounts that may have plaintext or malformed passwords'

    def handle(self, *args, **options):
        User = get_user_model()
        suspects = []
        for u in User.objects.all():
            pwd = u.password or ''
            # Django hashed passwords contain algorithm$salt$hash (have at least two $)
            if pwd.count('$') < 2:
                suspects.append((u.username, pwd))

        if not suspects:
            self.stdout.write(self.style.SUCCESS('No suspicious passwords found.'))
            return

        self.stdout.write(self.style.WARNING('Suspicious user password entries:'))
        for username, pwd in suspects:
            self.stdout.write(f'- {username}: {pwd[:60]}')
