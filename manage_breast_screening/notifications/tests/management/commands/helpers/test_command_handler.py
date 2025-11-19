from unittest.mock import MagicMock

import pytest
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.helpers.command_handler import (
    CommandHandler,
)


def test_command_handler_yields():
    mock = MagicMock()
    with CommandHandler.command_handler("SomeJob"):
        mock.do_stuff("this")
        mock.do_more_stuff("that")

    mock.do_stuff.assert_called_once_with("this")
    mock.do_more_stuff.assert_called_once_with("that")


def test_command_handler_logs_and_raises(mock_insights_logger):
    mock = MagicMock()
    an_exception = Exception("Nooooo!")
    mock.do_more_stuff.side_effect = an_exception

    with pytest.raises(CommandError) as exc_info:
        with CommandHandler.command_handler("SomeJob"):
            mock.do_stuff("this")
            mock.do_more_stuff("that")
    mock_insights_logger.assert_called_once_with(f"SomeJobError: {an_exception}")
    assert "Nooooo!" in str(exc_info.value)


def test_command_handler_logs_success(mock_insights_logger):
    mock = MagicMock()
    with CommandHandler.command_handler("SomeJob"):
        mock.do_stuff("this")
        mock.do_more_stuff("that")

    mock_insights_logger.assert_called_once_with(
        event_name="SomeJobCompleted", message="SomeJob completed successfully"
    )
