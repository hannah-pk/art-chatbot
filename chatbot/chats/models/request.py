from django.db import models
from chats.models import Conversation
from django.core.validators import RegexValidator, MaxLengthValidator, MinLengthValidator

target_params = {
    'colour_palette':['mood','image','number'],
    'edit_image': ['image', 'mood']
}

class Request(models.Model):
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE,related_name='request')
    instruction = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)])
    needs_image = models.BooleanField(default=False)
    params = models.JSONField()

    def set_instructions(self,new_instruction):
        self.instruction = new_instruction
        self.save()

    def add_params(self,param_name, param):
        self.params[param_name] = param
        self.save()

    def has_enough_params(self):
        if self.instruction=="colour_palette":
            if 'mood' in self.params.keys:
                mood = self.params['mood']
            if 'image' in self.params.keys:
                image = self.params['image']

    