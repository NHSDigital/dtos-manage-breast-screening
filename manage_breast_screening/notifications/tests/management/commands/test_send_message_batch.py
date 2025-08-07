import uuid
from datetime import datetime, timedelta
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests

from manage_breast_screening.notifications.api_client import ApiClient
from manage_breast_screening.notifications.management.commands.command_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    TZ_INFO,
    Command,
    CommandError,
)
from manage_breast_screening.notifications.models import Message, MessageBatch
from manage_breast_screening.notifications.tests.factories import AppointmentFactory


@patch.object(
    ApiClient, "send_message_batch", return_value=MagicMock(spec=requests.Response)
)
@patch.object(MessageBatchHelpers, "mark_batch_as_sent")
class TestSendMessageBatch:
    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.mark.django_db
    def test_handle_with_a_batch_to_send(
        self, mock_mark_batch_as_sent, mock_send_message_batch, routing_plan_id
    ):
        """Test sending message batch with valid Appointment data"""
        mock_send_message_batch.return_value.status_code = 201

        appointment = AppointmentFactory(
            starts_at=datetime.today().replace(tzinfo=TZ_INFO)
        )

        subject = Command()

        subject.handle(**{"routing_plan_id": routing_plan_id})

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert (
            Message.objects.filter(
                appointment=appointment, batch=message_batches[0]
            ).count()
            == 1
        )
        mock_mark_batch_as_sent.assert_called_once_with(message_batches[0], ANY)

    @pytest.mark.django_db
    def test_handle_with_nothing_to_send(
        self, mock_send_message_batch, routing_plan_id
    ):
        """Test that no MessageBatch or Message records are created when no appointments need notifications"""
        Command().handle(**{"routing_plan_id": routing_plan_id})

        assert MessageBatch.objects.count() == 0
        assert Message.objects.count() == 0

    @pytest.mark.django_db
    def test_handle_with_appointments_inside_schedule_window(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        routing_plan_id,
        monkeypatch,
    ):
        """Test that appointments with date inside the schedule period are notified"""
        mock_send_message_batch.return_value.status_code = 201
        appointment = AppointmentFactory(
            starts_at=datetime.now().replace(tzinfo=TZ_INFO)
            + timedelta(weeks=4, days=4)
        )

        subject = Command()

        subject.handle(**{"routing_plan_id": routing_plan_id})

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert (
            Message.objects.filter(
                appointment=appointment, batch=message_batches[0]
            ).count()
            == 1
        )
        mock_mark_batch_as_sent.assert_called_once_with(message_batches[0], ANY)

    @pytest.mark.django_db
    def test_handle_with_appointments_outside_schedule_window(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        routing_plan_id,
        monkeypatch,
    ):
        """Test that appointments with date inside the schedule period are notified"""
        AppointmentFactory(
            starts_at=datetime.now().replace(tzinfo=TZ_INFO)
            + timedelta(weeks=4, days=5)
        )

        subject = Command()

        subject.handle(**{"routing_plan_id": routing_plan_id})

        assert MessageBatch.objects.count() == 0
        assert Message.objects.count() == 0
        mock_mark_batch_as_sent.assert_not_called()

    @pytest.mark.django_db
    def test_handle_with_cancelled_appointments(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        routing_plan_id,
        monkeypatch,
    ):
        """Test that that cancelled appointments are not notified"""
        mock_send_message_batch.return_value.status_code = 201

        valid_appointment = AppointmentFactory(
            starts_at=datetime.today().replace(tzinfo=TZ_INFO)
        )

        _cancelled_appointment = AppointmentFactory(
            starts_at=datetime.today().replace(tzinfo=TZ_INFO), status="C"
        )

        subject = Command()

        subject.handle(**{"routing_plan_id": routing_plan_id})

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        messages = Message.objects.filter(batch=message_batches[0])
        assert messages.count() == 1
        assert messages[0].appointment == valid_appointment

    @pytest.mark.django_db
    def test_handle_with_failing_notifications(
        self, mark_batch_as_sent, mock_send_message_batch, routing_plan_id
    ):
        """Test that message batches which fail to send are marked correctly"""
        mock_send_message_batch.return_value.status_code = 400
        appointment = AppointmentFactory(
            starts_at=datetime.now().replace(tzinfo=TZ_INFO)
            + timedelta(weeks=4, days=4)
        )

        Command().handle(**{"routing_plan_id": routing_plan_id})

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert message_batches[0].status == "failed"
        messages = Message.objects.filter(
            appointment=appointment, batch=message_batches[0]
        )
        assert messages.count() == 1
        assert messages[0].status == "failed"

    def test_handle_with_error(self, mock_send_message_batch, routing_plan_id):
        """Test that errors are caught and raised as CommandErrors"""
        with pytest.raises(CommandError):
            Command().handle()
