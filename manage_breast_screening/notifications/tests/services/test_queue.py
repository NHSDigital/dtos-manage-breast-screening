from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.notifications.services.queue import Queue


class TestQueue:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("QUEUE_STORAGE_CONNECTION_STRING", "qqq111")

    @pytest.fixture
    def mock_queue_client(self):
        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            mock_client = MagicMock()
            queue_client.from_connection_string.return_value = mock_client
            yield mock_client

    def test_queue_is_created(self):
        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            mock_client = MagicMock()
            queue_client.from_connection_string.return_value = mock_client

            Queue("new-queue")

            queue_client.from_connection_string.assert_called_once_with(
                "qqq111", "new-queue"
            )
            mock_client.create_queue.assert_called_once()

    def test_add_to_queue(self, mock_queue_client):
        Queue("new-queue").add("a message")

        mock_queue_client.send_message.assert_called_once_with("a message")

    def test_message_status_updates_queue(self):
        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            mock_client = MagicMock()
            queue_client.from_connection_string.return_value = mock_client

            Queue.MessageStatusUpdates().add("some data")

            queue_client.from_connection_string.assert_called_once_with(
                "qqq111", "message-status-updates"
            )
            mock_client.create_queue.assert_called_once()
            mock_client.send_message.assert_called_once_with("some data")

    def test_failed_message_batches_queue(self):
        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            mock_client = MagicMock()
            queue_client.from_connection_string.return_value = mock_client

            Queue.RetryMessageBatches().add("some data")

            queue_client.from_connection_string.assert_called_once_with(
                "qqq111", "retry-message-batches"
            )
            mock_client.create_queue.assert_called_once()
            mock_client.send_message.assert_called_once_with("some data")

    def test_items_method_receives_messages(self, mock_queue_client):
        mock_queue_client.receive_messages.return_value = ["this", "that"]

        assert Queue("new-queue").items(limit=100) == ["this", "that"]

        mock_queue_client.receive_messages.assert_called_once_with(max_messages=100)

    def test_item_method_receives_messages(self, mock_queue_client):
        mock_queue_client.receive_message.return_value = ["this"]

        assert Queue("new-queue").item() == ["this"]

        mock_queue_client.receive_message.assert_called_once_with()

    def test_delete_deletes_message(self, mock_queue_client):
        Queue("new-queue").delete("this message")

        mock_queue_client.delete_message.assert_called_once_with("this message")
