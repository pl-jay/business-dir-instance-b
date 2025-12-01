# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text="Optional, used for password resets.")
    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "accept_terms")
