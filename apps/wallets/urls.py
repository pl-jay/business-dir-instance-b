from django.urls import path
from .views import challenge, verify,wallet_status

urlpatterns = [
    path("challenge/", challenge, name="wallet_challenge"),
    path("verify/", verify, name="wallet_verify"),
    path("status/", wallet_status, name="wallet_status"),
]
