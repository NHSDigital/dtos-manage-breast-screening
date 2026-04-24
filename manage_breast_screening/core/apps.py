from os import environ
from pathlib import Path

from django.apps import AppConfig

from manage_breast_screening.core.services.application_insights_logging import (
    ApplicationInsightsLogging,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_deployed_to = environ.get("DEPLOYED_TO")
_env_flags = _REPO_ROOT / f"flags.{_deployed_to}.yml" if _deployed_to else None
_FLAGS_YAML = (
    _env_flags if _env_flags and _env_flags.exists() else _REPO_ROOT / "flags.yml"
)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "manage_breast_screening.core"

    def ready(self):
        super().ready()
        ApplicationInsightsLogging().configure_azure_monitor()
        from manage_breast_screening.core.feature_flags import setup_feature_flags

        setup_feature_flags(_FLAGS_YAML)
