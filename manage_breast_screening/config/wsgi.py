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
    "DJANGO_SETTINGS_MODULE", "manage_breast_screening.config.settings"
)

application = get_wsgi_application()

# Warm up the database connection pool so the first user request does not pay
# the pool initialisation + Azure AD token cost.
#
# Without this, the psycopg3 pool is created lazily on the first DB access —
# which means the first real request incurs a TCP+TLS+IMDS+Postgres-auth
# round-trip (typically 5–30 s in Azure Container Apps after an idle period).
#
# Gunicorn does not preload the app by default, so this code runs once in
# each worker process before it starts accepting connections.
_logger = logging.getLogger(__name__)
try:
    from django.db import connection

    connection.ensure_connection()
    connection.close()
    _logger.info("Database connection pool warmed up")
except Exception:
    _logger.warning("Database connection pool warmup failed", exc_info=True)
