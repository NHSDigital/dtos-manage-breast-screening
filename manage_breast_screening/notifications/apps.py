from django.apps import AppConfig

from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "manage_breast_screening.notifications"

    def ready(self) -> None:
        ApplicationInsightsLogging().configure_azure_monitor()
        return super().ready()
