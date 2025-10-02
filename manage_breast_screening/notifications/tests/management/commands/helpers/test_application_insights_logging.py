from unittest.mock import MagicMock, patch

from manage_breast_screening.notifications.management.commands.helpers.application_insights_logging import (
    ApplicationInsightsLogging,
)


@patch(
    "manage_breast_screening.notifications.management.commands.helpers.application_insights_logging.configure_azure_monitor",
    return_value=MagicMock(),
)
@patch(
    "manage_breast_screening.notifications.management.commands.helpers.application_insights_logging.logging"
)
class TestApplicationInsightsLogging:
    def test_raise_exception(self, mock_logging, mock_configure_azure):
        ApplicationInsightsLogging().raise_an_exception("CustomError")
        mock_configure_azure.assert_called_with(
            logger_name="manbrs-notifications-local"
        )
        mock_logging.getLogger.assert_called_with("manbrs-notifications-local")
        mock_logging.getLogger.return_value.exception.assert_called_with(
            "CustomError", stack_info=True
        )
