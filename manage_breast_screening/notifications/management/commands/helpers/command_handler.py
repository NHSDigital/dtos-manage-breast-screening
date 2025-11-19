from contextlib import contextmanager

from django.core.management.base import CommandError

from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


class CommandHandler:
    @contextmanager
    @staticmethod
    def command_handler(command_name):
        try:
            yield
        except Exception as e:
            ApplicationInsightsLogging().exception(f"{command_name}Error: {e}")
            raise CommandError(e)
        else:
            ApplicationInsightsLogging().custom_event(
                event_name=f"{command_name}Completed",
                message=f"{command_name} completed successfully",
            )
