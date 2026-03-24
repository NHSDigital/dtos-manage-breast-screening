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

# Warm up the Jinja2 template cache so the first user request does not pay
# the PackageLoader traversal cost (~11 s in Azure Container Apps due to
# slower container filesystem I/O compared to local development).
#
# Rendering the base layout template forces Jinja2 to compile and cache
# all inherited and imported templates (NHS UK Frontend components etc.)
# that are loaded from the nhsuk_frontend_jinja package via PackageLoader.
_logger = logging.getLogger(__name__)
try:
    from django.template.loader import render_to_string

    render_to_string("layout-app.jinja", {})
    _logger.info("Jinja2 template cache warmed up")
except Exception:
    _logger.warning("Jinja2 template cache warmup failed", exc_info=True)
