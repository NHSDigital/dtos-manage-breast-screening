import json
import re
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MESSAGE_PATH_REGEX,
    TZ_INFO,
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.models import (
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.tests.factories import (
    MessageBatchFactory,
    MessageFactory,
)


class TestMessageBatchHelpers:
    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.mark.django_db
    def test_mark_messages_as_sent(self):
        message_1 = MessageFactory(status="scheduled")
        message_2 = MessageFactory(status="scheduled")
        message_batch = MessageBatchFactory(status="scheduled")
        message_batch.messages.set([message_1, message_2])
        message_batch.save()

        mock_response_json = {
            "data": {
                "id": "notify_id",
                "attributes": {
                    "messages": [
                        {"messageReference": message_1.id, "id": "id_1"},
                        {"messageReference": message_2.id, "id": "id_2"},
                    ]
                },
            }
        }

        MessageBatchHelpers.mark_batch_as_sent(
            message_batch=message_batch, response_json=mock_response_json
        )

        actual_message_1 = Message.objects.filter(id=message_1.id).first()
        assert actual_message_1 is not None
        assert actual_message_1.notify_id == "id_1"
        assert actual_message_1.status == "delivered"

        actual_message_2 = Message.objects.filter(id=message_2.id).first()
        assert actual_message_2 is not None
        assert actual_message_2.notify_id == "id_2"
        assert actual_message_2.status == "delivered"

        actual_message_batch = MessageBatch.objects.filter(id=message_batch.id).first()
        assert actual_message_batch is not None
        assert actual_message_batch.notify_id == "notify_id"
        assert actual_message_batch.status == "sent"

    @pytest.mark.parametrize("status_code", [401, 403, 404, 405, 406, 413, 415, 422])
    @pytest.mark.django_db
    def test_mark_batch_as_failed_with_unrecoverable_failures(
        self, status_code, routing_plan_id
    ):
        """Test that message batches which fail to send are marked correctly"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_response.json.return_value = notify_errors
        mock_now = datetime(2023, 1, 31, 0, 0, 0, tzinfo=TZ_INFO)

        message = MessageFactory(status="scheduled")
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)
        message_batch.messages.set([message])
        message_batch.save()

        with patch(
            "manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = mock_now
            MessageBatchHelpers.mark_batch_as_failed(message_batch, mock_response)

        message_batch.refresh_from_db()
        assert message_batch.status == "failed_unrecoverable"
        assert message_batch.nhs_notify_errors == notify_errors
        assert message_batch.messages.count() == 1
        assert message_batch.messages.all()[0].status == "failed"
        assert message_batch.messages.all()[0].sent_at == mock_now

    @pytest.mark.parametrize("status_code", [408, 425, 429, 500, 503, 504])
    @pytest.mark.django_db
    def test_mark_batch_as_failed_with_recoverable_failures(
        self, status_code, routing_plan_id
    ):
        """Test that message batches which fail to send are marked correctly"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_response.json.return_value = notify_errors
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.mark_batch_as_failed(
                message_batch, mock_response, retry_count=1
            )

            message_batch.refresh_from_db()
            assert message_batch.status == "failed_recoverable"
            assert message_batch.nhs_notify_errors == notify_errors
            queue_instance.add.assert_called_once_with(
                json.dumps(
                    {"message_batch_id": str(message_batch.id), "retry_count": 1}
                )
            )

    @patch.object(MessageBatchHelpers, "process_validation_errors")
    @pytest.mark.django_db
    def test_mark_batch_as_failed_with_validation_failure(
        self, mock_validation_method, routing_plan_id
    ):
        """Test that message batches with validation error are handled"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_response.json.return_value = notify_errors
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.mark_batch_as_failed(message_batch, mock_response, 1)

            mock_validation_method.assert_called_once_with(message_batch, 1)

    @pytest.mark.django_db
    def test_remove_validation_errors(self, routing_plan_id):
        """Test that messages which are invalid are removed from the message batch"""
        notify_errors = {
            "errors": [
                {
                    "status": 400,
                    "source": {
                        "pointer": "/data/attributes/messages/1/recipient/nhsNumber"
                    },
                }
            ]
        }
        message_1 = MessageFactory()
        message_2 = MessageFactory()
        message_3 = MessageFactory()
        message_batch = MessageBatchFactory(
            routing_plan_id=routing_plan_id,
            messages=[message_1, message_2, message_3],
            nhs_notify_errors=notify_errors,
        )

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.process_validation_errors(message_batch)

        message_batch.refresh_from_db()
        assert message_batch.status == "failed_recoverable"
        messages = message_batch.messages.all()
        assert messages.count() == 2
        assert messages[0] == message_1
        assert messages[1] == message_3

        message_2.refresh_from_db()
        assert message_2.batch is None

    @pytest.mark.django_db
    def test_save_errors_to_invalid_messages(self, routing_plan_id):
        """Test that messages which are invalid are updated with their nhs error"""
        message_1_errors = [
            {
                "status": 400,
                "source": {
                    "pointer": "/data/attributes/messages/0/recipient/nhsNumber"
                },
            }
        ]
        message_2_errors = [
            {
                "status": 400,
                "source": {
                    "pointer": "/data/attributes/messages/1/recipient/nhsNumber"
                },
            },
            {
                "status": 400,
                "source": {
                    "pointer": "/data/attributes/messages/1/recipient/nhsNumber"
                },
            },
        ]
        message_3_errors = [
            {
                "status": 400,
                "source": {
                    "pointer": "/data/attributes/messages/2/recipient/nhsNumber"
                },
            },
        ]
        notify_errors = {
            "errors": [
                *message_1_errors,
                *message_2_errors,
                *message_3_errors,
            ]
        }

        message_1 = MessageFactory()
        message_2 = MessageFactory()
        message_3 = MessageFactory()
        message_4 = MessageFactory()
        message_batch = MessageBatchFactory(
            routing_plan_id=routing_plan_id,
            messages=[message_1, message_2, message_3, message_4],
            nhs_notify_errors=notify_errors,
        )

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.process_validation_errors(message_batch)

        message_batch.refresh_from_db()
        assert message_batch.messages.all().count() == 1

        message_1.refresh_from_db()
        assert message_1.nhs_notify_errors == message_1_errors

        message_2.refresh_from_db()
        assert message_2.nhs_notify_errors == message_2_errors

        message_3.refresh_from_db()
        assert message_3.nhs_notify_errors == message_3_errors

        message_4.refresh_from_db()
        assert message_4.batch == message_batch

    @pytest.mark.django_db
    def test_add_altered_batch_back_to_queue(self, routing_plan_id):
        """Test that processing validation errors adds altered message batches back to retry queue"""
        notify_errors = {
            "errors": [
                {
                    "status": 400,
                    "source": {
                        "pointer": "/data/attributes/messages/1/recipient/nhsNumber"
                    },
                }
            ]
        }
        message_1 = MessageFactory()
        message_2 = MessageFactory()
        message_batch = MessageBatchFactory(
            routing_plan_id=routing_plan_id,
            messages=[message_1, message_2],
            nhs_notify_errors=notify_errors,
        )

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.process_validation_errors(message_batch, 1)

            queue_instance.add.assert_called_once_with(
                json.dumps(
                    {"message_batch_id": str(message_batch.id), "retry_count": 1}
                )
            )

    @pytest.mark.django_db
    def test_mark_batch_as_failed_for_non_json_error(self, routing_plan_id):
        """Test for non json response when retrying batch"""
        message = MessageFactory()
        message_batch = MessageBatchFactory(
            routing_plan_id=routing_plan_id,
            messages=[message],
        )
        mock_response = MagicMock(spec=requests.Response)
        mock_response.json.side_effect = Exception("Not JSON")
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance

            MessageBatchHelpers.mark_batch_as_failed(message_batch, mock_response)

        message_batch.refresh_from_db()
        assert message_batch.nhs_notify_errors == {"errors": "Internal Server Error"}
        assert (
            message_batch.status == MessageBatchStatusChoices.FAILED_RECOVERABLE.value
        )

    def test_validation_errors_regex_matches_expected_pointer(self):
        """
        Test the regex used to match the source pointer will recognise expected result from a 400 error from NHS Notify API
         https://digital.nhs.uk/developer/api-catalogue/nhs-notify#post-/v1/message-batches
        """
        api_pointer = "/data/attributes/messages/3/recipient/nhsNumber"

        message_index_result = re.search(MESSAGE_PATH_REGEX, api_pointer)

        assert int(message_index_result.group(0)) == 3
