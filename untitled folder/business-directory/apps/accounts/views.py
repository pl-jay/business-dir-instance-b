# apps/accounts/views.py
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.urls import reverse
from .forms import SignupForm
from django.conf import settings
from django.http import Http404

if not getattr(settings, "ALLOW_SIGNUP", True):
    raise Http404()  # or redirect with a message

def signup_view(request):
    if request.user.is_authenticated:
        return redirect("directory:list")  # or wherever

    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log in right after signup
            messages.success(request, "Welcome! Your account was created.")
            next_url = request.GET.get("next") or reverse("directory:list")
            return redirect(next_url)
    else:
        form = SignupForm()

    return render(request, "registration/signup.html", {"form": form})

from django.shortcuts import render

def terms_views(request):
    return render(request, "legal/terms.html")

def privacy_views(request):
    return render(request, "legal/privacy.html")
