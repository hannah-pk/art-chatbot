from django.core.management.base import BaseCommand
from chats.cleanup import cleanup_anonymous_conversations


class Command(BaseCommand):
    help = "Manually delete anonymous conversations that have been inactive for more than 1 hour."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run")
        result = cleanup_anonymous_conversations(dry_run=dry_run)

        if result["found_count"] == 0:
            self.stdout.write(self.style.SUCCESS("No stale anonymous conversations found."))
            return

        self.stdout.write(f"Found {result['found_count']} stale anonymous conversation(s).")
        if dry_run:
            if result.get("deleted_ids"):
                self.stdout.write("IDs that would be deleted: " + ",".join(str(i) for i in result.get("deleted_ids", [])))
            return

        self.stdout.write(self.style.SUCCESS(f"Deleted {result['deleted_count']} objects as part of {result['found_count']} conversation(s)."))