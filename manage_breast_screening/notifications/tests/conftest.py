from unittest.mock import MagicMock

import pytest

from manage_breast_screening.core.services.application_insights_logging import (
    ApplicationInsightsLogging,
)
from manage_breast_screening.core.services.command_handler import (
    CommandHandler,
)


@pytest.fixture
def base_module_str() -> str:
    return "manage_breast_screening.notifications"


@pytest.fixture
def commands_module_str(base_module_str) -> str:
    return f"{base_module_str}.management.commands"


@pytest.fixture(autouse=True)
def mock_insights_logger(request, monkeypatch):
    if "skip_insights_mock" in request.keywords:
        return
    mock_insights_logger = MagicMock()
    monkeypatch.setattr(ApplicationInsightsLogging, "exception", mock_insights_logger)
    monkeypatch.setattr(
        ApplicationInsightsLogging, "custom_event_warning", mock_insights_logger
    )
    monkeypatch.setattr(
        ApplicationInsightsLogging, "custom_event_info", mock_insights_logger
    )
    return mock_insights_logger


@pytest.fixture
def mock_command_handler(request, monkeypatch):
    mock_command_handler = MagicMock()
    monkeypatch.setattr(CommandHandler, "handle", mock_command_handler)
    return mock_command_handler
