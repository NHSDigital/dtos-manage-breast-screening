from unittest.mock import MagicMock, patch

import requests

from manage_breast_screening.notifications.api_client import ApiClient
from manage_breast_screening.notifications.management.commands.command_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.management.commands.send_failed_message_batch import (
    Command,
)
from manage_breast_screening.notifications.services.queue import Queue


@patch.object(
    ApiClient, "send_message_batch", return_value=MagicMock(spec=requests.Response)
)
@patch.object(Queue, "RetryMessageBatches", return_value=MagicMock(spec=Queue))
@patch.object(MessageBatchHelpers, "mark_batch_as_sent")
class TestSendFailedMessageBatch:
    # @pytest.mark.django_db
    # def test_handle_batch_not_found(
    #     self, mock_mark_batch_as_sent, mock_retry_message_batches, mock_send_message_batch
    # ):
    #     subject = Command()
    #     batch_id = uuid.uuid4()

    #     with pytest.raises(CommandError) as error:
    #         subject.handle()

    #     assert (
    #         str(error.value)
    #         == f"Message Batch with id {batch_id} and status of 'failed' not found"
    #     )

    # @pytest.mark.django_db
    # def test_not_failed_yet(self, mock_mark_batch_as_sent, mock_retry_message_batches, mock_senmock_retry_message_batchesd_message_batch):
    #     subject = Command()
    #     batch_id = uuid.uuid4()
    #     _scheduled_batch = MessageBatchFactory(id=batch_id)

    #     with pytest.raises(CommandError) as error:
    #         subject.handle()

    #     assert (
    #         str(error.value)
    #         == f"Message Batch with id {batch_id} and status of 'failed' not found"
    #     )

    # @pytest.mark.django_db
    # def test_server_error_when_resending_batch(
    #     self, mock_mark_batch_as_sent, mock_retry_message_batches, mock_send_message_batch, monkeypatch
    # ):
    #     mock_send_message_batch.return_value.status_code = 500
    #     mock_send_message_batch.return_value.reason = "Request timed out"
    #     subject = Command()
    #     batch_id = uuid.uuid4()
    #     _failed_batch = MessageBatchFactory(id=batch_id, status="failed")

    #     with pytest.raises(CommandError) as error:
    #         subject.handle()

    #     assert (
    #         str(error.value)
    #         == f"Message Batch with id {batch_id} not sent: 500, Request timed out"
    #     )

    # @pytest.mark.django_db
    # def test_successfully_resends_batch(
    #     self, mock_mark_batch_as_sent, mock_retry_message_batches, mock_send_message_batch, monkeypatch
    # ):
    #     mock_send_message_batch.return_value.status_code = 201
    #     subject = Command()
    #     batch_id = uuid.uuid4()
    #     failed_batch = MessageBatchFactory(id=batch_id, status="failed")

    #     subject.handle()

    #     mock_mark_batch_as_sent.assert_called_once_with(
    #         message_batch=failed_batch, response_json=ANY
    #     )

    def test_no_batches_in_queue(
        self,
        mock_mark_batch_as_sent,
        mock_retry_message_batches,
        mock_send_message_batch,
    ):
        subject = Command()

        subject.handle()

        assert mock_retry_message_batches.delete.call_count == 0
