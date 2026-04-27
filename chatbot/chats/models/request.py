from django.db import models
from chats.models import Conversation
from django.core.validators import MaxLengthValidator, MinLengthValidator

class Request(models.Model):
    """
    Represents the current ongoing request within a conversation.
    There should only ever be at most one ongoing request in a conversation.

    Contains the instruction and related parameters, as well as some information on which parameter may be needed to successfully perform the instruction
    """
    conversation = models.OneToOneField(Conversation, on_delete=models.CASCADE,related_name='request')
    instruction = models.TextField(validators=[MinLengthValidator(3), MaxLengthValidator(200)],null=True,blank=True)
    needs_image = models.BooleanField(default=False)
    params = models.JSONField(default=dict,blank=True)

    def set_instruction(self,new_instruction):
        """
        Sets the instruction for the current request
        """
        self.instruction = new_instruction
        self.save()

    def get_instruction(self):
        return self.instruction

    def add_params(self,param_name, param):
        """
        Adds a parameter key and value to the dictionary of parameters
        """
        self.params[param_name] = param
        self.save()

    def get_params(self):
        return self.params

    def set_image_needed(self,value):
        """
        Sets whether or not an image is needed for this particular request
        """
        self.needs_image = value
        self.save()

    def get_image_needed(self):
        return self.needs_image

    def missing_params(self):
        """
        Finds whether there are any missing parameters that would prevent the successful execution of the instruction
        """
        mood = self.params['mood']
        if mood is None:
            return 'mood'
        if self.needs_image:
            if 'image' not in self.params.keys():
                return 'image'
        return None

    