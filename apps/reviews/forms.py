"""Forms for the reviews app.

This module defines custom forms for creating and updating reviews, as well
as reporting reviews.  The default ModelForm behaviour is extended to
support additional fields (e.g. sub‑ratings, anonymity) and multiple
attachments.  Attachments are saved in the corresponding view rather
than within the form to allow the review instance to be persisted
before file creation.
"""

from __future__ import annotations

from typing import Any, Iterable

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ClearableFileInput
from .widgets import MultiFileInput
from .models import Review, ReviewAttachment, ReviewReport


class ReviewForm(forms.ModelForm):
    """Form for creating a new review.

    Includes additional sub‑ratings, anonymity flags and the ability to
    upload multiple attachments.  The overall rating field allows half
    values via the HTML ``step=0.5`` attribute but is rounded to the
    nearest integer when saved to the model.
    """

    attachments = forms.FileField(
        required=False,
        widget=MultiFileInput(attrs={"multiple": True}),
        help_text="Attach photos or videos to your review (optional).",
    )

    class Meta:
        model = Review
        fields = [
            "rating",
            "rating_service",
            "rating_value",
            "rating_quality",
            "rating_cleanliness",
            "comment",
            "is_anonymous",
            "display_name",
        ]
        widgets = {
            # Allow half‑star increments on the client side.  The model
            # stores integers; cleaning converts the float to int.
            "rating": forms.NumberInput(attrs={"min": 1, "max": 5, "step": 0.5, "class": "form-control"}),
            "rating_service": forms.Select(choices=Review.RATING_CHOICES, attrs={"class": "form-select"}),
            "rating_value": forms.Select(choices=Review.RATING_CHOICES, attrs={"class": "form-select"}),
            "rating_quality": forms.Select(choices=Review.RATING_CHOICES, attrs={"class": "form-select"}),
            "rating_cleanliness": forms.Select(choices=Review.RATING_CHOICES, attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_rating(self) -> int:
        """Round the rating to the nearest integer for storage."""
        rating = self.cleaned_data.get("rating")
        if rating is None:
            raise ValidationError("Rating is required.")
        try:
            value = float(rating)
        except (TypeError, ValueError):
            raise ValidationError("Invalid rating.")
        # Round halves up to nearest whole number
        return int(round(value))

    def clean_comment(self) -> str:
        comment = self.cleaned_data.get("comment") or ""
        if comment.strip() and len(comment.strip()) < 20:
            raise ValidationError("Please enter at least 20 characters for your review.")
        return comment


class ReviewUpdateForm(ReviewForm):
    """Form for updating an existing review.

    Reuses the logic from ``ReviewForm``.  Attachments can be added
    during editing; existing attachments remain associated with the
    review and are not removed automatically.
    """

    class Meta(ReviewForm.Meta):
        model = Review
        fields = ReviewForm.Meta.fields


class ReviewReportForm(forms.ModelForm):
    """Form for reporting/flagging a review."""

    class Meta:
        model = ReviewReport
        fields = ["reason", "comment"]
        widgets = {
            "reason": forms.Select(attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
        }