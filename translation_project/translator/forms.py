from django import forms

class TranslationForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, required=False)
    file = forms.FileField(required=False)
