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
