import json
from datetime import datetime, timedelta
from unittest.mock import ANY, MagicMock, patch

import pytest
import requests
from dateutil import relativedelta

from manage_breast_screening.notifications.management.commands.helpers.message_batch_helpers import (
    MessageBatchHelpers,
)
from manage_breast_screening.notifications.management.commands.helpers.routing_plan import (
    RoutingPlan,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    TZ_INFO,
    Command,
    CommandError,
)
from manage_breast_screening.notifications.models import Message, MessageBatch
from manage_breast_screening.notifications.services.api_client import ApiClient
from manage_breast_screening.notifications.tests.factories import AppointmentFactory


@patch.object(
    ApiClient, "send_message_batch", return_value=MagicMock(spec=requests.Response)
)
@patch.object(MessageBatchHelpers, "mark_batch_as_sent")
@pytest.mark.time_machine(datetime.today() + relativedelta.relativedelta(weekday=0))
@pytest.mark.django_db
class TestSendMessageBatch:
    def test_handle_with_a_batch_to_send(
        self, mock_mark_batch_as_sent, mock_send_message_batch
    ):
        """Test sending message batch with valid Appointment data"""
        mock_send_message_batch.return_value.status_code = 201

        appointment = AppointmentFactory(starts_at=datetime.now(tz=TZ_INFO))
        routing_plan_id = RoutingPlan.for_episode_type(appointment.episode_type).id

        Command().handle()

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert (
            Message.objects.filter(
                appointment=appointment, batch=message_batches[0]
            ).count()
            == 1
        )
        mock_mark_batch_as_sent.assert_called_once_with(message_batches[0], ANY)

    def test_handle_for_all_routing_plans(
        self, mock_mark_batch_as_sent, mock_send_message_batch
    ):
        """Test sending message batch with valid Appointment data"""
        mock_send_message_batch.return_value.status_code = 201
        routing_plans = RoutingPlan.all()

        appointment1 = AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO), episode_type="R"
        )
        appointment2 = AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO), episode_type="F"
        )

        Command().handle()

        message_batches = MessageBatch.objects.all()
        assert message_batches.count() == 2
        assert str(message_batches[0].routing_plan_id) == routing_plans[0].id
        assert str(message_batches[1].routing_plan_id) == routing_plans[1].id
        assert Message.objects.filter(
            appointment=appointment2, batch=message_batches[0]
        ).exists()
        assert Message.objects.filter(
            appointment=appointment1, batch=message_batches[1]
        ).exists()
        mock_mark_batch_as_sent.assert_any_call(message_batches[0], ANY)
        mock_mark_batch_as_sent.assert_any_call(message_batches[1], ANY)

    def test_handle_with_nothing_to_send(
        self, mock_mark_batch_as_sent, mock_send_message_batch
    ):
        """Test that no MessageBatch or Message records are created when no appointments need notifications"""
        Command().handle()

        assert MessageBatch.objects.count() == 0
        assert Message.objects.count() == 0

    def test_handle_with_appointments_inside_schedule_window(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        monkeypatch,
    ):
        """Test that appointments with date inside the schedule period are notified"""
        mock_send_message_batch.return_value.status_code = 201
        appointment = AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO) + timedelta(weeks=4)
        )
        routing_plan_id = RoutingPlan.for_episode_type(appointment.episode_type).id

        Command().handle()

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert (
            Message.objects.filter(
                appointment=appointment, batch=message_batches[0]
            ).count()
            == 1
        )
        mock_mark_batch_as_sent.assert_called_once_with(message_batches[0], ANY)

    def test_handle_with_appointments_outside_schedule_window(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        monkeypatch,
    ):
        """Test that appointments with date inside the schedule period are notified"""
        AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO) + timedelta(weeks=4, days=1)
        )

        Command().handle()

        assert MessageBatch.objects.count() == 0
        assert Message.objects.count() == 0
        mock_mark_batch_as_sent.assert_not_called()

    def test_handle_with_cancelled_appointments(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        monkeypatch,
    ):
        """Test that that cancelled appointments are not notified"""
        mock_send_message_batch.return_value.status_code = 201

        valid_appointment = AppointmentFactory(starts_at=datetime.now(tz=TZ_INFO))
        routing_plan_id = RoutingPlan.for_episode_type(
            valid_appointment.episode_type
        ).id

        _cancelled_appointment = AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO), status="C"
        )

        Command().handle()

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        messages = Message.objects.filter(batch=message_batches[0])
        assert messages.count() == 1
        assert messages[0].appointment == valid_appointment

    @pytest.mark.parametrize("status_code", [401, 403, 404, 405, 406, 413, 415, 422])
    def test_handle_with_unrecoverable_failures(
        self, mark_batch_as_sent, mock_send_message_batch, status_code
    ):
        """Test that message batches which fail to send are marked correctly"""
        mock_send_message_batch.return_value.status_code = status_code
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_send_message_batch.return_value.json.return_value = notify_errors
        appointment = AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO) + timedelta(weeks=4)
        )
        routing_plan_id = RoutingPlan.for_episode_type(appointment.episode_type).id

        Command().handle()

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert message_batches[0].status == "failed_unrecoverable"
        assert message_batches[0].nhs_notify_errors == notify_errors
        messages = Message.objects.filter(
            appointment=appointment, batch=message_batches[0]
        )
        assert messages.count() == 1
        assert messages[0].status == "failed"

    @pytest.mark.parametrize("status_code", [408, 425, 429, 500, 503, 504])
    def test_handle_with_recoverable_failures(
        self, mark_batch_as_sent, mock_send_message_batch, status_code
    ):
        """Test that message batches which fail to send are marked correctly"""
        notify_errors = {"errors": [{"some-error": "details"}]}
        mock_send_message_batch.return_value.status_code = status_code
        mock_send_message_batch.return_value.json.return_value = notify_errors

        appointment = AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO) + timedelta(weeks=4)
        )
        routing_plan_id = RoutingPlan.for_episode_type(appointment.episode_type).id

        with patch(
            "manage_breast_screening.notifications.views.Queue.RetryMessageBatches"
        ) as mock_queue:
            queue_instance = MagicMock()
            mock_queue.return_value = queue_instance
            Command().handle()

        message_batches = MessageBatch.objects.filter(routing_plan_id=routing_plan_id)
        assert message_batches.count() == 1
        assert message_batches[0].status == "failed_recoverable"
        assert message_batches[0].nhs_notify_errors == notify_errors
        queue_instance.add.assert_called_once_with(
            json.dumps(
                {"message_batch_id": str(message_batches[0].id), "retry_count": 0}
            )
        )

    def test_handle_does_nothing_on_weekend(
        self, mock_mark_batch_as_sent, mock_send_message_batch, time_machine
    ):
        AppointmentFactory(starts_at=datetime.now(tz=TZ_INFO) + timedelta(weeks=4))
        time_machine.move_to(datetime.now() + relativedelta.relativedelta(weekday=5))

        Command().handle()

        mock_send_message_batch.assert_not_called()

        time_machine.move_to(datetime.now() + relativedelta.relativedelta(weekday=6))

        Command().handle()

        mock_send_message_batch.assert_not_called()

    def test_handle_with_non_first_time_appointment(
        self,
        mock_mark_batch_as_sent,
        mock_send_message_batch,
        monkeypatch,
    ):
        """Test that appointments with date inside the schedule period are notified"""
        AppointmentFactory(
            starts_at=datetime.now(tz=TZ_INFO) + timedelta(weeks=4),
            number="2",
        )

        Command().handle()

        assert MessageBatch.objects.count() == 0
        assert Message.objects.count() == 0
        mock_mark_batch_as_sent.assert_not_called()

    def test_handle_with_error(self, mock_mark_batch_as_sent, mock_send_message_batch):
        """Test that errors are caught and raised as CommandErrors"""
        with patch.object(RoutingPlan, "all", side_effect=Exception("Nooooo!")):
            with pytest.raises(CommandError):
                Command().handle()
