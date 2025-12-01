"""
Application configuration for the onchain app.
"""

from django.apps import AppConfig


class OnchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.onchain'
