"""
WSGI config for the patriot project.

This exposes the WSGI callable as a module-level variable named ``application``.
It allows web servers to serve your Django project. See
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/ for more information.
"""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'patriot.settings')

application = get_wsgi_application()