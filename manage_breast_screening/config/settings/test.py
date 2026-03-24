# ruff: noqa: E402, F401, F403, F405
# Settings for running the test suite.
# Loads .env.test as the baseline config. Any env vars already set in the
# environment take precedence (e.g. CI sets DATABASE_* via workflow env vars).
# .env is never loaded here — only .env.test.
#
# Add overrides here only when the value is a data structure (e.g. STORAGES)
# or requires programmatic modification (e.g. MIDDLEWARE.remove(...)).

from pathlib import Path

from dotenv import load_dotenv

_CONFIG_DIR = (
    Path(__file__).resolve().parent.parent
)  # = manage_breast_screening/config/

load_dotenv(_CONFIG_DIR / ".env.test")

from .base import *

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "dicom": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {"base_url": "/dicom/"},
    },
}

MIDDLEWARE.remove("whitenoise.middleware.WhiteNoiseMiddleware")
