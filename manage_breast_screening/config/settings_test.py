# ruff: noqa: F403, F405
from os import environ

# Force the personas setting on, ensuring that the URL will be included in
# the URLConf
environ["PERSONAS_ENABLED"] = "1"

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
