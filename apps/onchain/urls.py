"""
URL patterns for the onchain app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.OnChainListView.as_view(), name="list"),
    path("new/", views.OnChainCreateView.as_view(), name="create"),
    path("<int:pk>/", views.OnChainDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.OnChainUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.OnChainDeleteView.as_view(), name="delete"),
]
