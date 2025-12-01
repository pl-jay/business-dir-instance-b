"""
URL patterns for the ranking app.
"""

from django.urls import path
from .views import TopRated, MostReviewed30d
from . import views


urlpatterns = [
    path("", views.RankingListView.as_view(), name="list"),
    path("new/", views.RankingCreateView.as_view(), name="create"),
    path("<int:pk>/", views.RankingDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.RankingUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.RankingDeleteView.as_view(), name="delete"),
    path("top-rated/", TopRated.as_view(), name="rankings_top_rated"),
    path("most-reviewed/", MostReviewed30d.as_view(), name="rankings_most_reviewed"),
]
