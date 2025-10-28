from unittest.mock import MagicMock

import pytest

from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


@pytest.fixture
def base_module_str() -> str:
    return "manage_breast_screening.notifications"


@pytest.fixture
def commands_module_str(base_module_str) -> str:
    return f"{base_module_str}.management.commands"


@pytest.fixture
def mock_insights_logger(monkeypatch):
    mock_insights_logger = MagicMock()
    monkeypatch.setattr(ApplicationInsightsLogging, "exception", mock_insights_logger)
    return mock_insights_logger
