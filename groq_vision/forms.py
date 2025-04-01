from django import forms

class ImageForm(forms.Form):
    image = forms.ImageField(required = False)
    query = forms.CharField(max_length = 500, required = True)
    