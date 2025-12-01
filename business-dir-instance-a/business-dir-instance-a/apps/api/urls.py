from django.urls import path
from .views import api_businesses, api_business_onchain, api_review_signature_presence

urlpatterns = [
    path("businesses", api_businesses),
    path("businesses/<slug:slug>/onchain", api_business_onchain),
    path("reviews/<int:pk>/signature", api_review_signature_presence),
]
