# ruff: noqa: E402, F401, F403, F405
# Settings for local development.
# Loads manage_breast_screening/config/.env before importing base settings.
# Assumes developers have a local .env file (copy from .env.tpl to get started).

from pathlib import Path

from dotenv import load_dotenv

_CONFIG_DIR = (
    Path(__file__).resolve().parent.parent
)  # = manage_breast_screening/config/
load_dotenv(_CONFIG_DIR / ".env")

from .base import *
