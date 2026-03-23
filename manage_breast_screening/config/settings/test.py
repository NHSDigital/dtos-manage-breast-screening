# ruff: noqa: E402, F401, F403, F405
# Settings for running the test suite.
# Loads .env.test with override=True to guarantee deterministic values
# regardless of any env vars the developer has set in their shell.
# .env is never loaded here — only .env.test.
#
# All simple string/boolean config should be specified in .env.test, not here.
# Add overrides here only when the value is a data structure (e.g. STORAGES)
# or requires programmatic modification (e.g. MIDDLEWARE.remove(...)).

from pathlib import Path

from dotenv import load_dotenv

_CONFIG_DIR = (
    Path(__file__).resolve().parent.parent
)  # = manage_breast_screening/config/

load_dotenv(_CONFIG_DIR / ".env.test", override=True)

from .base import *

# STORAGES is a Python dict — can't be expressed in .env.test
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "dicom": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {"base_url": "/dicom/"},
    },
}

# List mutation — can't be done in .env.test
MIDDLEWARE.remove("whitenoise.middleware.WhiteNoiseMiddleware")
