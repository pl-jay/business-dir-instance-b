"""Test suite for the reviews app extensions.

These tests exercise the extended functionality added to the Review
model and associated views: sub‑ratings, anonymity, attachments,
voting and reporting.  They serve as a regression guard to ensure
future refactoring does not break key behaviours.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.directory.models import Business
from .models import Review, ReviewAttachment, ReviewVote, ReviewReport


class ReviewExtendedTests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(username="reviewer", password="pass")
        self.other = User.objects.create_user(username="other", password="pass")
        # Minimal business for reviews
        self.business = Business.objects.create(name="Test Biz", slug="test-biz")

    def test_review_has_extended_fields_and_text_alias(self) -> None:
        r = Review.objects.create(business=self.business, user=self.user, rating=5, comment="Nice")
        # Ensure optional sub‑ratings exist
        self.assertTrue(hasattr(r, "rating_service"))
        self.assertEqual(r.text, r.comment)

    def test_create_review_with_attachment(self) -> None:
        self.client.login(username="reviewer", password="pass")
        url = reverse("reviews:create_for_business", kwargs={"business_slug": self.business.slug})
        file_data = SimpleUploadedFile("photo.jpg", b"abc", content_type="image/jpeg")
        resp = self.client.post(
            url,
            {
                "rating": 4,
                "comment": "Great place! At least twenty characters.",
                "attachments": file_data,
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        review = Review.objects.get()
        self.assertEqual(review.attachments.count(), 1)

    def test_vote_endpoint_toggle(self) -> None:
        # Create a review
        review = Review.objects.create(business=self.business, user=self.user, rating=4)
        self.client.login(username="other", password="pass")
        vote_url = reverse("reviews:vote", kwargs={"review_id": review.id})
        # Upvote
        resp = self.client.post(vote_url, {"is_helpful": "true"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        review.refresh_from_db()
        self.assertEqual(review.votes.filter(is_helpful=True).count(), 1)
        # Toggle same vote (should remove)
        resp = self.client.post(vote_url, {"is_helpful": "true"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(review.votes.count(), 0)
        # Downvote
        resp = self.client.post(vote_url, {"is_helpful": "false"}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(review.votes.filter(is_helpful=False).count(), 1)

    def test_report_view_creates_or_updates_report(self) -> None:
        review = Review.objects.create(business=self.business, user=self.user, rating=4)
        self.client.login(username="other", password="pass")
        report_url = reverse("reviews:report", kwargs={"review_id": review.id})
        # First report
        resp = self.client.post(report_url, {"reason": "spam", "comment": "Looks fake"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(ReviewReport.objects.filter(review=review, reporter=self.other).count(), 1)
        # Update existing report
        resp = self.client.post(report_url, {"reason": "offensive", "comment": "Abusive"}, follow=True)
        self.assertEqual(ReviewReport.objects.filter(review=review, reporter=self.other).count(), 1)
        rr = ReviewReport.objects.get(review=review, reporter=self.other)
        self.assertEqual(rr.reason, "offensive")
        self.assertEqual(rr.comment, "Abusive")