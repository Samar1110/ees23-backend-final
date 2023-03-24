from django.forms import ModelForm
from .models import BroadCast_Email

class PostForm(ModelForm):
    class Meta:
        model = BroadCast_Email
        fields = ['subject','created','message']