import json
import uuid
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests

from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.management.commands.retry_failed_message_batch import (
    Command,
    CommandError,
)
from manage_breast_screening.notifications.services.api_client import ApiClient
from manage_breast_screening.notifications.services.application_insights_logging import (
    ApplicationInsightsLogging,
)
from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.tests.factories import MessageBatchFactory


@pytest.fixture(autouse=True)
def setup(monkeypatch):
    monkeypatch.setenv("NOTIFICATIONS_BATCH_RETRY_LIMIT", "5")
    monkeypatch.setenv("NOTIFICATIONS_BATCH_RETRY_DELAY", "10")


@patch.object(
    ApiClient, "send_message_batch", return_value=MagicMock(spec=requests.Response)
)
@patch.object(Queue, "RetryMessageBatches", return_value=MagicMock(spec=Queue))
@patch.object(MessageBatchHelpers, "mark_batch_as_sent")
@patch.object(MessageBatchHelpers, "mark_batch_as_failed")
class TestRetryFailedMessageBatch:
    @pytest.fixture(autouse=True)
    def mock_insights_logger(self, monkeypatch):
        mock_insights_logger = MagicMock()
        monkeypatch.setattr(
            ApplicationInsightsLogging, "exception", mock_insights_logger
        )
        return mock_insights_logger

    @pytest.mark.django_db
    def test_handle_batch_not_found(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
    ):
        batch_id = uuid.uuid4()
        mock_retry_message_batches.return_value.item.return_value.content = json.dumps(
            {"message_batch_id": str(batch_id)}
        )
        subject = Command()

        with pytest.raises(CommandError) as error:
            subject.handle()

        assert (
            str(error.value)
            == f"Message Batch with id {batch_id} and status of 'failed_recoverable' not found"
        )

        assert mock_retry_message_batches.delete.call_count == 0

    @pytest.mark.django_db
    def test_not_failed_yet(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
    ):
        subject = Command()
        batch_id = uuid.uuid4()
        _scheduled_batch = MessageBatchFactory(id=batch_id)
        mock_retry_message_batches.return_value.item.return_value.content = json.dumps(
            {"message_batch_id": str(batch_id)}
        )

        with pytest.raises(CommandError) as error:
            subject.handle()

        assert (
            str(error.value)
            == f"Message Batch with id {batch_id} and status of 'failed_recoverable' not found"
        )

    @pytest.mark.django_db
    def test_server_error_when_resending_batch(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
        monkeypatch,
    ):
        mock_send_message_batch.return_value.status_code = 500
        mock_send_message_batch.return_value.reason = "Request timed out"
        subject = Command()
        batch_id = uuid.uuid4()
        failed_batch = MessageBatchFactory(id=batch_id, status="failed_recoverable")
        mock_retry_message_batches.return_value.item.return_value.content = json.dumps(
            {"message_batch_id": str(batch_id), "retry_count": 1}
        )

        subject.handle()

        mock_mark_batch_as_failed.assert_called_once_with(
            message_batch=failed_batch,
            response=mock_send_message_batch.return_value,
            retry_count=2,
        )

    @pytest.mark.django_db
    def test_successfully_resends_batch(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
        monkeypatch,
    ):
        mock_send_message_batch.return_value.status_code = 201
        subject = Command()
        batch_id = uuid.uuid4()
        failed_batch = MessageBatchFactory(id=batch_id, status="failed_recoverable")
        mocked_item = MagicMock()
        mock_retry_message_batches.return_value.item = mocked_item
        mocked_item.return_value.content = json.dumps(
            {"message_batch_id": str(batch_id), "retry_count": 1}
        )

        subject.handle()

        mock_mark_batch_as_sent.assert_called_once_with(
            message_batch=failed_batch, response_json=ANY
        )
        mock_retry_message_batches.return_value.delete.assert_called_with(mocked_item())

    @pytest.mark.django_db
    def test_no_batches_in_queue(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
    ):
        mock_retry_message_batches.return_value.item.return_value = None
        subject = Command()

        subject.handle()

        mock_retry_message_batches.return_value.delete.assert_not_called

        # reset mock
        mock_retry_message_batches.return_value.item.return_value = MagicMock()

    @pytest.mark.django_db
    def test_batch_with_retry_count_more_than_5_is_marked_as_failed_unrecoverable(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
    ):
        subject = Command()
        batch_id = uuid.uuid4()
        _failed_batch = MessageBatchFactory(id=batch_id, status="failed_recoverable")

        mock_retry_message_batches.return_value.item.return_value.content = json.dumps(
            {"message_batch_id": str(batch_id), "retry_count": 5}
        )

        with pytest.raises(CommandError) as error:
            subject.handle()

        assert (
            str(error.value)
            == f"Message Batch with id {batch_id} not sent: Retry limit exceeded"
        )

    @pytest.mark.django_db
    def test_calls_insights_logger_if_exception_raised(
        self,
        mock_mark_batch_as_failed,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
        mock_insights_logger,
    ):
        subject = Command()
        batch_id = uuid.uuid4()
        _failed_batch = MessageBatchFactory(id=batch_id, status="failed_recoverable")

        mock_retry_message_batches.return_value.item.return_value.content = json.dumps(
            {"message_batch_id": str(batch_id), "retry_count": 5}
        )

        with pytest.raises(CommandError):
            subject.handle()

        mock_insights_logger.assert_called_with(
            f"RetryFailedMessageBatchError: Message Batch with id {str(batch_id)} not sent: Retry limit exceeded"
        )
