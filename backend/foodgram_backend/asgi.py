"""
ASGI config for foodgram_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

Formoreinformation on this file, see
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram_backend.settings')

application = get_asgi_application()
