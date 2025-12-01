"""
Models for the business directory application.

Defines the ``Business`` model with a slug field for human‑friendly URLs.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse


class Business(models.Model):
    """A simple model representing a local business."""

    name = models.CharField(max_length=200,db_index=True)
    category = models.CharField(max_length=120, blank=True,db_index=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    slug = models.SlugField(unique=True, max_length=220)
    created_at = models.DateTimeField(auto_now_add=True,db_index=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="businesses",
        null=True,
        blank=True,
    )
    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("directory:detail", kwargs={"slug": self.slug})
