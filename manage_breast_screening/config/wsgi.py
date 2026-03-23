"""
WSGI config for manage_breast_screening project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import logging
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "manage_breast_screening.config.settings.production"
)

application = get_wsgi_application()

# Warm up the database connection so the first user request does not pay
# the TCP+TLS+IMDS+Postgres-auth round-trip cost.
#
# Django reuses persistent connections (CONN_MAX_AGE), but does not create
# them eagerly. Without this, the first real request in each gunicorn worker
# would pay that cost (typically 1–5 s after an idle period in Azure).
#
# Gunicorn does not preload the app by default, so this code runs once in
# each worker process before it starts accepting connections.
_logger = logging.getLogger(__name__)
try:
    from django.db import connection

    connection.ensure_connection()
    connection.close()
    _logger.info("Database connection warmed up")
except Exception:
    _logger.warning("Database connection warmup failed", exc_info=True)

# Warm up the Jinja2 template cache so the first user request does not pay
# the PackageLoader traversal cost (~11 s in Azure Container Apps due to
# slower container filesystem I/O compared to local development).
#
# Rendering the base layout template forces Jinja2 to compile and cache
# all inherited and imported templates (NHS UK Frontend components etc.)
# that are loaded from the nhsuk_frontend_jinja package via PackageLoader.
try:
    from django.template.loader import render_to_string

    render_to_string("layout-app.jinja", {})
    _logger.info("Jinja2 template cache warmed up")
except Exception:
    _logger.warning("Jinja2 template cache warmup failed", exc_info=True)
