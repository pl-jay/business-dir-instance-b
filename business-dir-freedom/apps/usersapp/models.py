"""
Models for the usersapp.
"""

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model


class Profile(models.Model):
    """Additional information for a Django user account."""

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return self.user.get_username()  # type: ignore[no-any-return]

    def get_absolute_url(self) -> str:
        return reverse("usersapp:detail", kwargs={"pk": self.pk})
