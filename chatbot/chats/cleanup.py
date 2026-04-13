from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db.models import Max, Q

from .models import Conversation, Request
    

def cleanup_user_image(seconds: int | None = None, dry_run: bool = False):
    """
    Deletes the user image from the database and also resets (deletes any ongoing requests for that conversation)
    """
    seconds = 1800 #30 minutes
    cutoff = timezone.now() - timedelta(seconds=seconds)
    qs = Conversation.objects.filter(user_identity__startswith="user:")
    qs = qs.annotate(last_msg=Max("messages__created_at"))

    stale = qs.filter(Q(last_msg__lt=cutoff) | Q(last_msg__isnull=True, created_at__lt=cutoff))
    total = stale.count()
    if total == 0:
        return {"found_count": 0, "deleted_count": 0, "deleted_ids": []}
    if dry_run:
        ids = list(stale.values_list("id", flat=True))
        return {"found_count": total, "deleted_count": 0, "deleted_ids": ids}
    deleted_count = 0
    for conversation in stale:
        request = Request.objects.filter(conversation=conversation)
        request.delete()
        for m in conversation.messages.exclude(image__isnull=True):
            try:
                m.image.delete()
                deleted_count += 1
            except Exception as e:
                print(f"faced an issue deleting image from message {m.id}: {e}")
                continue
    return {"found_count": total, "deleted_count": deleted_count, "deleted_ids": []}


def cleanup_anonymous_conversations(seconds: int | None = None, dry_run: bool = False):
    """Delete anonymous conversations older than 1 hour. Returns dict with found_count, deleted_count, deleted_ids (if dry_run)."""
    seconds = 1800  # always 30 minutes
    cutoff = timezone.now() - timedelta(seconds=seconds)

    qs = Conversation.objects.filter(user_identity__startswith="anon:")
    qs = qs.annotate(last_msg=Max("messages__created_at"))

    stale = qs.filter(Q(last_msg__lt=cutoff) | Q(last_msg__isnull=True, created_at__lt=cutoff))

    total = stale.count()
    if total == 0:
        return {"found_count": 0, "deleted_count": 0, "deleted_ids": []}

    if dry_run:
        ids = list(stale.values_list("id", flat=True))
        return {"found_count": total, "deleted_count": 0, "deleted_ids": ids}

    # perform delete
    deleted_info = stale.delete()
    # deleted_info[1] contains per-model counts, deleted_info[0] is total objects
    return {"found_count": total, "deleted_count": deleted_info[0], "deleted_ids": []}
