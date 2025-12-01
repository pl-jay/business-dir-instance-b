"""
URL patterns for the usersapp.
"""

from django.urls import path
from . import views


urlpatterns = [
    path("", views.ProfileListView.as_view(), name="list"),
    path("new/", views.ProfileCreateView.as_view(), name="create"),
    path("<int:pk>/", views.ProfileDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ProfileUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ProfileDeleteView.as_view(), name="delete"),
]
