# apps/accounts/urls.py
from django.urls import path
from .views import signup_view,privacy_views,terms_views

urlpatterns = [
    path("signup/", signup_view, name="signup"),
    path("terms/", terms_views, name="terms"),
    path("privacy/", privacy_views, name="privacy"),
]
