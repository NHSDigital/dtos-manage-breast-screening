from contextlib import contextmanager

from django.core.management.base import CommandError

from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


@contextmanager
def exception_handler(command_name):
    try:
        yield
    except Exception as e:
        ApplicationInsightsLogging().exception(f"{command_name}Error: {e}")
        raise CommandError(e)
