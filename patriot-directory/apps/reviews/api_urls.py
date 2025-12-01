from django.urls import path
from . import api_views  # see next section

app_name = "reviews_api"

urlpatterns = [
    path("<int:pk>/digest/", api_views.review_digest, name="digest"),
    path("<int:pk>/sign/", api_views.review_sign, name="sign"),
]
