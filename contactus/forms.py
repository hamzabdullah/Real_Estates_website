
from django import forms
from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Your full name",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "Your email address",
            }),
            "subject": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "How can we help?",
            }),
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "placeholder": "Write your message here...",
                "rows": 5,
            }),
        }
