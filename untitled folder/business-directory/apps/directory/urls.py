"""
URL patterns for the business directory application.
"""

from django.urls import path

from . import views


urlpatterns = [
    path("", views.BusinessListView.as_view(), name="list"),
    path("api/", views.business_list_api, name="api"),
    path("b/new/", views.BusinessCreateView.as_view(), name="create"),
    path("b/<slug:slug>/", views.BusinessDetailView.as_view(), name="detail"),
    path("b/<slug:slug>/edit/", views.BusinessUpdateView.as_view(), name="edit"),
    path("b/<slug:slug>/delete/", views.BusinessDeleteView.as_view(), name="delete"),
]
