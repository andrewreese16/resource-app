from django import forms 
from .models import Resource

class ResourceForm(forms.ModelForm):
  class Meta:
    model = Resource
    fields = ['name', 'description', 'category', 'contact_info', 'location']