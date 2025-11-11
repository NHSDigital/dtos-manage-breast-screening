from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.notifications.management.commands.collect_metrics import (
    Command,
)
from manage_breast_screening.notifications.services.metrics import Metrics


class TestCollectMetrics:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "test")

    @patch(f"{Command.__module__}.Queue")
    def test_handle_sends_queue_lengths(self, mock_queue):
        mock_metrics_1 = MagicMock(spec=Metrics)
        mock_metrics_2 = MagicMock(spec=Metrics)
        mock_queue.RetryMessageBatches.return_value.queue_name = "queue 1"
        mock_queue.RetryMessageBatches.return_value.get_message_count.return_value = 8
        mock_queue.MessageStatusUpdates.return_value.queue_name = "queue 2"
        mock_queue.MessageStatusUpdates.return_value.get_message_count.return_value = 2

        with patch(
            f"{Command.__module__}.Metrics",
            side_effect=[mock_metrics_1, mock_metrics_2],
        ) as mock_metrics_class:
            Command().handle()

        mock_metrics_class.assert_any_call(
            "queue 1", "messages", "Queue length", "test"
        )
        mock_metrics_class.assert_any_call(
            "queue 2", "messages", "Queue length", "test"
        )
        mock_metrics_1.add.assert_called_once_with("queue_name", 8)
        mock_metrics_2.add.assert_called_once_with("queue_name", 2)
