"""
Admin configuration for the usersapp.
"""

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "website", "location", "created_at")
    search_fields = ("user__username", "location")
