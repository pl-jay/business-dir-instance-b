"""
Models for the reviews app.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.directory.models import Business


class Review(models.Model):
    """A review for a business left by a user."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="reviews")
    # Overall rating on a 1–5 scale. To maintain backwards compatibility
    # with existing aggregates (e.g. Business.avg_rating), we store the
    # primary rating as an integer.  Half‑star inputs are rounded when
    # saving via the form.
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    # Optional sub‑ratings for specific aspects of the experience.  When
    # provided, these help users leave more granular feedback without
    # affecting the aggregate rating stored above.
    rating_service = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_value = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_quality = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    rating_cleanliness = models.PositiveSmallIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    comment = models.TextField(blank=True)
    # Display name override and anonymity flag.  When is_anonymous is
    # True the reviewer’s username is not shown and display_name (if
    # provided) will be used instead.
    display_name = models.CharField(max_length=100, blank=True)
    is_anonymous = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.business.name} – {self.rating}/5 by {self.user}"  # type: ignore[str-bytes-safe]

    def get_absolute_url(self) -> str:
        return reverse("reviews:detail", kwargs={"pk": self.pk})

    # Maintain backwards compatibility for legacy templates/admin that
    # reference `review.text`. Historically the comment field was named
    # `text`; this property ensures those references continue to work.
    @property
    def text(self) -> str:
        return self.comment


class ReviewAttachment(models.Model):
    """File attachments associated with a review.

    Supports images or videos uploaded by the reviewer. Files are
    uploaded to the ``review_attachments/`` directory under the default
    MEDIA_ROOT.  Removing a review cascades and deletes associated
    attachments on the filesystem (subject to Django’s file storage
    settings).
    """

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="review_attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"Attachment {self.pk} for review {self.review_id}"


class ReviewVote(models.Model):
    """Stores a helpful/not helpful vote for a review by a user.

    A user may vote once per review; votes can be toggled between
    helpful and not helpful.  The ``is_helpful`` flag distinguishes
    positive and negative votes.
    """

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="review_votes")
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("review", "user")
        indexes = [models.Index(fields=["review", "user"])]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"Vote by {self.user_id} on review {self.review_id}: {'helpful' if self.is_helpful else 'not helpful'}"


class ReviewReport(models.Model):
    """Represents a user report/flag for a review.

    Allows users to flag inappropriate content or violations of
    guidelines.  Each user may submit at most one report per review;
    subsequent submissions update the existing record.  The moderator
    can later review and act on these reports (not implemented here).
    """

    REASON_CHOICES = [
        ("spam", "Spam or irrelevant"),
        ("offensive", "Offensive or abusive"),
        ("fake", "Fake or misleading"),
        ("other", "Other"),
    ]

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="reports")
    reporter = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="review_reports")
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("review", "reporter")
        indexes = [models.Index(fields=["review", "reporter"])]

    def __str__(self) -> str:  # pragma: no cover - simple repr
        return f"Report by {self.reporter_id} on review {self.review_id}"

class OwnerReply(models.Model):
    review = models.OneToOneField("Review", on_delete=models.CASCADE, related_name="owner_reply")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.owner} to review {self.review_id}"


class ReviewSignature(models.Model):
    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="signature")  # 1:1 keeps it simple
    signer_address = models.CharField(max_length=42, db_index=True)
    message_hash = models.CharField(max_length=66)  # 0x + 64 hex
    signature = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["signer_address", "created_at"])]