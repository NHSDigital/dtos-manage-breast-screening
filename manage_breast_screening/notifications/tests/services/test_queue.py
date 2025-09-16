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
                "qqq111", "notifications-message-status-updates"
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
                "qqq111", "notifications-message-batch-retries"
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

        mock_queue_client.receive_message.assert_called_once()

    def test_delete_deletes_message(self, mock_queue_client):
        Queue("new-queue").delete("this message")

        mock_queue_client.delete_message.assert_called_once_with("this message")

    def test_queue_initialises_using_managed_identity_credentials(self, monkeypatch):
        monkeypatch.setenv("STORAGE_ACCOUNT_NAME", "mystorageaccount")
        monkeypatch.setenv("QUEUE_MI_CLIENT_ID", "my-mi-id")
        mock_mi_cred = MagicMock()

        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            with patch(
                "manage_breast_screening.notifications.services.queue.ManagedIdentityCredential"
            ) as managed_identity_constructor:
                managed_identity_constructor.return_value = mock_mi_cred

                Queue("new-queue")

                queue_client.assert_called_once_with(
                    "https://mystorageaccount.queue.core.windows.net",
                    queue_name="new-queue",
                    credential=mock_mi_cred,
                )
                managed_identity_constructor.assert_called_once_with(
                    client_id="my-mi-id"
                )

    def test_update_queue_prefers_queue_name_from_env(self, monkeypatch):
        monkeypatch.setenv("STATUS_UPDATES_QUEUE_NAME", "updates")
        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            mock_client = MagicMock()
            queue_client.from_connection_string.return_value = mock_client

            Queue.MessageStatusUpdates()

            queue_client.from_connection_string.assert_called_once_with(
                "qqq111", "updates"
            )

    def test_retry_queue_prefers_queue_name_from_env(self, monkeypatch):
        monkeypatch.setenv("RETRY_QUEUE_NAME", "retries")
        with patch(
            "manage_breast_screening.notifications.services.queue.QueueClient"
        ) as queue_client:
            Queue.RetryMessageBatches()

            queue_client.from_connection_string.assert_called_once_with(
                "qqq111", "retries"
            )
