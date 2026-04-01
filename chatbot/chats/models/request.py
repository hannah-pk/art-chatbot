from django.db import models
from chats.models import Conversation
from django.core.validators import MaxLengthValidator, MinLengthValidator

target_params = {
    'colour_palette':['mood','image','number'],
    'edit_image': ['image', 'mood']
}

class Request(models.Model):
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE,related_name='request')
    instruction = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)],null=True,blank=True)
    needs_image = models.BooleanField(default=False)
    params = models.JSONField(default=dict,blank=True)

    def set_instruction(self,new_instruction):
        self.instruction = new_instruction
        self.save()

    def add_params(self,param_name, param):
        self.params[param_name] = param
        self.save()

    def set_image_needed(self,value):
        self.needs_image = value
        self.save()

    def missing_params(self):
        mood = self.params['mood']
        if mood is None:
            return 'mood'
        if self.needs_image:
            if 'image' not in self.params.keys():
                return 'image'
        return None

    