"""
Admin configuration for the business directory.
"""

from django.contrib import admin

from .models import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Admin interface for the ``Business`` model."""

    list_display = ("name", "category", "phone", "website")
    search_fields = ("name", "category", "address", "phone", "website")
    prepopulated_fields = {"slug": ("name",)}
