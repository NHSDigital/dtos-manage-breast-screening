from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.notifications.management.commands.collect_metrics import (
    Command,
)


class TestCollectMetrics:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "test")

    @patch(f"{Command.__module__}.Queue")
    @patch(f"{Command.__module__}.Metrics")
    def test_handle_sends_queue_lengths(self, mock_metrics_class, mock_queue):
        mock_retry = MagicMock()
        mock_retry.queue_name = "retry_queue"
        mock_retry.get_message_count.return_value = 8

        mock_status = MagicMock()
        mock_status.queue_name = "status_queue"
        mock_status.get_message_count.return_value = 2

        mock_queue.RetryMessageBatches.return_value = mock_retry
        mock_queue.MessageStatusUpdates.return_value = mock_status

        mock_metrics_instance = MagicMock()
        mock_metrics_class.return_value = mock_metrics_instance

        Command().handle()

        mock_metrics_class.assert_called_once_with("test")

        mock_metrics_instance.set_gauge_value.assert_any_call(
            "queue_size_retry_queue",
            "messages",
            "Queue length",
            8,
        )
        mock_metrics_instance.set_gauge_value.assert_any_call(
            "queue_size_status_queue",
            "messages",
            "Queue length",
            2,
        )

        assert mock_metrics_instance.set_gauge_value.call_count == 2
