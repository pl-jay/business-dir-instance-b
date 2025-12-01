# apps/accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required for verification and password reset.")
    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy"
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2", "accept_terms")
