# ruff: noqa: F403, F405
from os import environ

# Force the personas settings off
# This can be switched to on when we start testing different roles
environ["PERSONAS_ENABLED"] = "0"

from .settings import *

SECRET_KEY = "testing"

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


MIDDLEWARE.remove(
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

if DEBUG:
    INSTALLED_APPS.remove("debug_toolbar")
    MIDDLEWARE.remove("debug_toolbar.middleware.DebugToolbarMiddleware")
    DEBUG_TOOLBAR = False
