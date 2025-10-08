import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command as CreateAppointments,
)
from manage_breast_screening.notifications.management.commands.retry_failed_message_batch import (
    Command as RetryFailedMessageBatch,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    Command as SendMessageBatch,
)
from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command as StoreMeshMessages,
)
from manage_breast_screening.notifications.models import (
    Appointment,
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
    MessageStatusChoices,
)
from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
class TestEndToEnd:
    @pytest.mark.django_db
    def test_get_from_mesh_and_send_message_batch(self, mock_jwt_encode, monkeypatch):
        Helpers().add_file_to_mesh_mailbox(
            f"{os.path.dirname(os.path.realpath(__file__))}/ABC_20250302091221_APPT_100.dat"
        )
        Queue.RetryMessageBatches().client.clear_messages()

        StoreMeshMessages().handle()

        today_dirname = datetime.today().strftime("%Y-%m-%d")
        CreateAppointments().handle(**{"date_str": today_dirname})

        appointments = Appointment.objects.filter(
            episode_type__in=["F", "G", "R", "S"],
            starts_at__lte=datetime.now() + timedelta(weeks=4),
            message__isnull=True,
            status="B",
        )
        assert len(appointments) == 3

        appointment_date = datetime.now() + timedelta(days=2)
        appointments.update(starts_at=appointment_date)

        # Respond with a 408 recoverable error
        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL",
            "http://localhost:8888/message/batch/recoverable-error",
        )

        SendMessageBatch().handle()

        failed_batches = MessageBatch.objects.filter(
            status=MessageBatchStatusChoices.FAILED_RECOVERABLE.value
        )

        assert failed_batches.count() == 1

        messages = Message.objects.filter(
            batch=failed_batches.first(),
        )

        assert messages.count() == 3

        # Respond with a 400 validation error
        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL",
            "http://localhost:8888/message/batch/validation-error",
        )

        RetryFailedMessageBatch().handle()

        failed_batches = MessageBatch.objects.filter(
            status=MessageBatchStatusChoices.FAILED_RECOVERABLE.value
        )

        assert failed_batches.first().messages.count() == 2

        invalid_messages = Message.objects.filter(
            status=MessageStatusChoices.FAILED.value
        ).all()
        assert invalid_messages.count() == 1
        assert (
            invalid_messages.first().nhs_notify_errors[0]["code"]
            == "CM_INVALID_NHS_NUMBER"
        )

        # Respond with 201 success
        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )

        RetryFailedMessageBatch().handle()

        sent_batches = MessageBatch.objects.filter(
            status=MessageBatchStatusChoices.SENT.value
        ).all()

        assert sent_batches.count() == 1
        assert sent_batches.first().messages.count() == 2

        assert len(Queue.RetryMessageBatches().peek()) == 0
