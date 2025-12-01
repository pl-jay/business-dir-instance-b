"""
Models for the ranking app.
"""

from django.db import models
from django.urls import reverse

from apps.directory.models import Business


class Ranking(models.Model):
    """A simple ranking score for a business."""

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="rankings")
    score = models.FloatField(help_text="Numeric score for this business, e.g. 0.0 – 5.0")
    comment = models.TextField(blank=True, help_text="Optional commentary on the score")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.business.name}: {self.score}"

    def get_absolute_url(self) -> str:
        return reverse("ranking:detail", kwargs={"pk": self.pk})
