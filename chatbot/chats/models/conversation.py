from django.db import models

class Conversation(models.Model):
    """
    A conversation that a user may have with the chatbot
    """
    title = models.CharField(max_length=100, default="New Conversation")
    user_identity = models.CharField(max_length=100, db_index=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title