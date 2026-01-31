from django.db import models
from chats.models import Conversation
from django.core.validators import RegexValidator, MaxLengthValidator, MinLengthValidator

target_params = {
    'colour_palette':['mood','image','number'],
    'edit_image': ['image', 'mood']
}

class Request(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    instruction = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])
    params = models.JSONField()

    def set_instructions(self,new_instruction):
        self.instruction = new_instruction
        self.save()

    def add_params(self,param_name, param):
        self.params[param_name] = param
        self.save()

    def has_enough_params(self):
        pass

    