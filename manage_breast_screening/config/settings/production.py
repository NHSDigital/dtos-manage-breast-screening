# ruff: noqa: F401, F403, F405
# Settings for production deployment.
# Environment variables are injected by Azure Container Apps / Key Vault at runtime.
# This module does not call load_dotenv — all required env vars must already be set.

from .base import *
