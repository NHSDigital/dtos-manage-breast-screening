from django.apps import AppConfig

from manage_breast_screening.core.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "manage_breast_screening.core"

    def ready(self):
        super().ready()
        ApplicationInsightsLogging().configure_azure_monitor()
