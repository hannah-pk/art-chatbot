from django.db import models

class Conversation(models.Model):
    title = models.CharField(max_length=100)
    user_identity = models.CharField(max_length=100, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title