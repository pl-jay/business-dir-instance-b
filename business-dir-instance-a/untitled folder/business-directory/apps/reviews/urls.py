"""
URL patterns for the reviews app.
"""

from django.urls import path
from . import views


urlpatterns = [
    path("", views.ReviewListView.as_view(), name="list"),
    path("new/<slug:business_slug>/", views.ReviewCreateView.as_view(), name="create_for_business"),
    path("<int:pk>/", views.ReviewDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ReviewUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ReviewDeleteView.as_view(), name="delete"),

    path("<int:review_id>/reply/new/", views.OwnerReplyCreateView.as_view(), name="reply_create"),
    path("reply/<int:pk>/edit/", views.OwnerReplyUpdateView.as_view(), name="reply_edit"),

    # AJAX endpoint to vote reviews as helpful or not.  Expects POST with
    # ``is_helpful=true`` or ``is_helpful=false`` and returns JSON.
    path("<int:review_id>/vote/", views.review_vote, name="vote"),

    # Flag/report a review.  Shows a form and persists a ReviewReport.
    path("<int:review_id>/report/", views.ReviewReportView.as_view(), name="report"),
]
