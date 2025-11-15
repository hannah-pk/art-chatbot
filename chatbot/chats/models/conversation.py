from django.db import models

class Conversation(models.Model):
    session_id = models.CharField(max_length=64,db_index=True)