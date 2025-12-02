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
        mock_status = MagicMock()
        mock_status.queue_name = "status_queue"
        mock_status.get_message_count.return_value = 2

        mock_queue.MessageStatusUpdates.return_value = mock_status

        Command().handle()

        metrics_instance = mock_metrics_class.return_value

        metrics_instance.set_gauge_value.assert_called_once_with(
            "queue_size_status_queue",
            "messages",
            "Queue length",
            2,
        )
