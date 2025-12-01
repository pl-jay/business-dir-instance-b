"""
Models for the business directory application.

Defines the ``Business`` model with a slug field for human‑friendly URLs.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db import models
from django.utils import timezone

class BusinessQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(status=Business.Status.APPROVED, is_deleted=False)

    def pending(self):
        return self.filter(status=Business.Status.PENDING, is_deleted=False)

    def rejected(self):
        return self.filter(status=Business.Status.REJECTED, is_deleted=False)

class Business(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

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

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="business_submissions",
    )
    submitted_at = models.DateTimeField(default=timezone.now, db_index=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="business_approvals",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default="")

    is_deleted = models.BooleanField(default=False)

    objects = BusinessQuerySet.as_manager()

    @property
    def is_published(self) -> bool:
        return self.status == self.Status.APPROVED and not self.is_deleted
