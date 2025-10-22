from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


@patch(
    "manage_breast_screening.notifications.services.application_insights_logging.configure_azure_monitor",
    return_value=MagicMock(),
)
@patch(
    "manage_breast_screening.notifications.services.application_insights_logging.logging"
)
class TestApplicationInsightsLogging:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("APPLICATIONINSIGHTS_LOGGER_NAME", "insights-logger")

    def test_configure_azure_monitor(
        self, mock_logging, mock_configure_azure, monkeypatch
    ):
        monkeypatch.setenv("APPLICATIONINSIGHTS_IS_ENABLED", "True")
        ApplicationInsightsLogging().configure_azure_monitor()
        mock_configure_azure.assert_called_with(logger_name="insights-logger")

    def test_getLogger(self, mock_logging, mock_configure_azure):
        ApplicationInsightsLogging().getLogger()
        mock_logging.getLogger.assert_called_with("insights-logger")

    def test_raise_exception(self, mock_logging, mock_configure_azure):
        ApplicationInsightsLogging().exception("CustomError")
        mock_logging.getLogger.assert_called_with("insights-logger")
        mock_logging.getLogger.return_value.exception.assert_called_with(
            "CustomError", stack_info=True
        )

    def test_custom_event(self, mock_logging, mock_configure_azure):
        ApplicationInsightsLogging().custom_event(
            "something went wrong", "custom-event"
        )
        mock_logging.getLogger.assert_called_with("insights-logger")
        mock_logging.getLogger.return_value.warning.assert_called_with(
            "something went wrong",
            extra={
                "microsoft.custom_event.name": "custom-event",
                "additional_attrs": "something went wrong",
            },
        )
