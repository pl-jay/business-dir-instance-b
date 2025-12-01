"""
URL patterns for the reviews app.
"""

from django.urls import path
from . import views


urlpatterns = [
    # The standalone review list page has been removed. All review interaction
    # occurs within the context of a business. See documentation for details.

    # Create a review for a given business slug. A ``next`` parameter may be
    # supplied in the query string to control where the user is redirected
    # after submitting or cancelling the form.
    path("new/<slug:business_slug>/", views.ReviewCreateView.as_view(), name="create_for_business"),

    # Individual review detail, edit and delete views. Note that these views
    # no longer link back to a global review list. Instead, they link back
    # to the business or to the referring page.
    path("<int:pk>/", views.ReviewDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", views.ReviewUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", views.ReviewDeleteView.as_view(), name="delete"),

    # Owner reply management.
    path("<int:review_id>/reply/new/", views.OwnerReplyCreateView.as_view(), name="reply_create"),
    path("reply/<int:pk>/edit/", views.OwnerReplyUpdateView.as_view(), name="reply_edit"),

    # AJAX endpoint to vote reviews as helpful or not.  Expects POST with
    # ``is_helpful=true`` or ``is_helpful=false`` and returns JSON.
    path("<int:review_id>/vote/", views.review_vote, name="vote"),

    # Flag/report a review.  Shows a form and persists a ReviewReport.
    path("<int:review_id>/report/", views.ReviewReportView.as_view(), name="report"),
]
