"""
WSGI config for caravaggio project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

from configurations.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "caravaggio_rest_api.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "development")

application = get_wsgi_application()
