import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.core.management.base import CommandError

from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command,
)
from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)


@patch(
    "manage_breast_screening.notifications.management.commands.store_mesh_messages.BlobStorage"
)
@patch(
    "manage_breast_screening.notifications.management.commands.store_mesh_messages.MeshInbox"
)
class TestStoreMeshMessages:
    @pytest.fixture(autouse=True)
    def mock_insights_logger(self, monkeypatch):
        mock_insights_logger = MagicMock()
        monkeypatch.setattr(
            ApplicationInsightsLogging, "exception", mock_insights_logger
        )
        return mock_insights_logger

    def test_handle_stores_blobs(self, mock_mesh_inbox, mock_blob_storage, monkeypatch):
        dirname = datetime.datetime.now().strftime("%Y-%m-%d")
        message1 = Mock()
        message1.filename = "file1"
        message1.read.return_value = "message1 content".encode("ASCII")
        message2 = Mock()
        message2.filename = "file2"
        message2.read.return_value = "message2 content".encode("ASCII")

        mock_inbox_context = mock_mesh_inbox.return_value.__enter__()

        mock_inbox_context.fetch_message_ids.return_value = ["id1", "id2"]
        mock_inbox_context.fetch_message.side_effect = [message1, message2]

        Command().handle()

        mock_inbox_context.acknowledge.assert_any_call("id1")
        mock_inbox_context.acknowledge.assert_any_call("id2")

        mock_blob_storage.return_value.add.assert_any_call(
            f"{dirname}/file1", "message1 content"
        )
        mock_blob_storage.return_value.add.assert_any_call(
            f"{dirname}/file2", "message2 content"
        )

    def test_handle_empty_inbox(self, mock_mesh_inbox, mock_blob_storage):
        mock_mesh_inbox.return_value.__enter__().fetch_message_ids.return_value = []

        Command().handle()

        mock_mesh_inbox.return_value.__enter__().acknowledge.assert_not_called()
        mock_blob_storage.return_value.add.assert_not_called()

    def test_handle_raises_command_error(self, mock_mesh_inbox, _x):
        mock_mesh_inbox.side_effect = Exception("Noooo!")

        with pytest.raises(CommandError):
            Command().handle()

    def test_calls_insights_logger_if_exception_raised(
        self,
        mock_mesh_inbox,
        _y,
        mock_insights_logger,
    ):
        mock_mesh_inbox.side_effect = Exception("inbox wrong")

        with pytest.raises(CommandError):
            Command().handle()

        mock_insights_logger.assert_called_with("StoreMeshMessagesError: inbox wrong")
