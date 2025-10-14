import hashlib
import hmac
import json
import os
import random
import string
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from django.test import TestCase
from test.support.os_helper import EnvironmentVarGuard

from manage_breast_screening.notifications.management.commands.create_appointments import (
    Command as CreateAppointments,
)
from manage_breast_screening.notifications.management.commands.retry_failed_message_batch import (
    Command as RetryFailedMessageBatch,
)
from manage_breast_screening.notifications.management.commands.save_message_status import (
    Command as SaveMessageStatus,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    Command as SendMessageBatch,
)
from manage_breast_screening.notifications.management.commands.store_mesh_messages import (
    Command as StoreMeshMessages,
)
from manage_breast_screening.notifications.models import (
    Appointment,
    ChannelStatus,
    Message,
    MessageBatch,
    MessageBatchStatusChoices,
    MessageStatus,
    MessageStatusChoices,
)
from manage_breast_screening.notifications.services.queue import Queue
from manage_breast_screening.notifications.tests.integration.helpers import Helpers


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
class TestEndToEnd(TestCase):
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        connection_string = Helpers().azurite_connection_string()
        self.env = EnvironmentVarGuard()
        self.env.set("DJANGO_ENV", "test")
        self.env.set("NHS_NOTIFY_APPLICATION_ID", "application_id")
        self.env.set("NHS_NOTIFY_API_KEY", "api_key")
        self.env.set("NBSS_MESH_HOST", "http://localhost:8700")
        self.env.set("NBSS_MESH_PASSWORD", "password")
        self.env.set("NBSS_MESH_SHARED_KEY", "TestKey")
        self.env.set("NBSS_MESH_INBOX_NAME", "X26ABC1")
        self.env.set("NBSS_MESH_CERT", "mesh-cert")
        self.env.set("NBSS_MESH_PRIVATE_KEY", "mesh-private-key")
        self.env.set("NBSS_MESH_CA_CERT", "mesh-ca-cert")
        self.env.set("BLOB_STORAGE_CONNECTION_STRING", connection_string)
        self.env.set("QUEUE_STORAGE_CONNECTION_STRING", connection_string)
        self.env.set("BLOB_CONTAINER_NAME", "nbss-appoinments-data")
        self.env.set("API_OAUTH_TOKEN_URL", "http://localhost:8888/token")
        self.env.set("API_OAUTH_API_KEY", "a1b2c3d4")
        self.env.set("NHS_NOTIFY_APPLICATION_ID", "application_id")
        self.env.set("NHS_NOTIFY_API_KEY", "api_key")

        Helpers().add_file_to_mesh_mailbox(
            f"{os.path.dirname(os.path.realpath(__file__))}/ABC_20250302091221_APPT_100.dat"
        )
        Queue.MessageStatusUpdates().client.clear_messages()
        Queue.RetryMessageBatches().client.clear_messages()

    @pytest.mark.django_db
    def test_all_commands_in_sequence(self, mock_jwt_encode):
        StoreMeshMessages().handle()

        today_dirname = datetime.today().strftime("%Y-%m-%d")
        CreateAppointments().handle(**{"date_str": today_dirname})

        appointments = Appointment.objects.filter(
            episode_type__in=["F", "G", "R", "S"],
            starts_at__lte=datetime.now() + timedelta(weeks=4),
            status="B",
        )

        appointment_date = datetime.now() + timedelta(days=2)
        appointments.update(starts_at=appointment_date)

        assert appointments.count() == 3

        # Respond with a 408 recoverable error
        self.env.set(
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
        self.env.set(
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
        self.env.set(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )

        RetryFailedMessageBatch().handle()

        sent_batches = MessageBatch.objects.filter(
            status=MessageBatchStatusChoices.SENT.value
        )

        assert sent_batches.count() == 1
        sent_batch = sent_batches.first()
        sent_messages = sent_batch.messages.all()
        assert sent_messages.count() == 2
        appointments_from_sent_messages = [m.appointment for m in sent_messages]

        assert appointments_from_sent_messages == [appointments[1], appointments[2]]
        assert len(Queue.RetryMessageBatches().peek()) == 0

        self.make_callbacks(sent_messages)

        SaveMessageStatus().handle()

        self.assert_status_updates(sent_messages)

    def assert_status_updates(self, sent_messages):
        message_status_updates = MessageStatus.objects.filter(
            message=sent_messages[0]
        ).all()
        assert message_status_updates.count() == 4
        assert message_status_updates[0].status == "sending"
        assert message_status_updates[1].status == "failed"
        assert message_status_updates[2].status == "sending"
        assert message_status_updates[3].status == "delivered"

        channel_status_updates = ChannelStatus.objects.filter(
            message=sent_messages[0]
        ).all()
        assert channel_status_updates.count() == 4
        assert channel_status_updates[0].channel == "nhsapp"
        assert channel_status_updates[0].status == "received"
        assert channel_status_updates[1].channel == "nhsapp"
        assert channel_status_updates[1].status == "unnotified"
        assert channel_status_updates[2].channel == "sms"
        assert channel_status_updates[2].status == "received"
        assert channel_status_updates[3].channel == "sms"
        assert channel_status_updates[3].status == "delivered"

        message_status_updates = MessageStatus.objects.filter(
            message=sent_messages[1]
        ).all()
        assert message_status_updates.count() == 6
        assert message_status_updates[0].status == "sending"
        assert message_status_updates[1].status == "failed"
        assert message_status_updates[2].status == "sending"
        assert message_status_updates[3].status == "failed"
        assert message_status_updates[4].status == "sending"
        assert message_status_updates[5].status == "delivered"

        channel_status_updates = ChannelStatus.objects.filter(
            message=sent_messages[1]
        ).all()
        assert channel_status_updates.count() == 6
        assert channel_status_updates[0].channel == "nhsapp"
        assert channel_status_updates[0].status == "received"
        assert channel_status_updates[1].channel == "nhsapp"
        assert channel_status_updates[1].status == "unnotified"
        assert channel_status_updates[2].channel == "sms"
        assert channel_status_updates[2].status == "received"
        assert channel_status_updates[3].channel == "sms"
        assert channel_status_updates[3].status == "permanent_failure"
        assert channel_status_updates[4].channel == "letter"
        assert channel_status_updates[4].status == "accepted"
        assert channel_status_updates[5].channel == "letter"
        assert channel_status_updates[5].status == "received"

    def make_callbacks(self, sent_messages):
        self.message_status_callback(sent_messages[0], "nhsapp", "sending")
        self.message_status_callback(sent_messages[0], "nhsapp", "failed")
        self.message_status_callback(sent_messages[0], "sms", "sending")
        self.message_status_callback(sent_messages[0], "sms", "delivered")
        self.channel_status_callback(sent_messages[0], "nhsapp", "sending", "received")
        self.channel_status_callback(sent_messages[0], "nhsapp", "failed", "unnotified")
        self.channel_status_callback(sent_messages[0], "sms", "sending", "received")
        self.channel_status_callback(sent_messages[0], "sms", "delivered", "delivered")

        self.message_status_callback(sent_messages[1], "nhsapp", "sending")
        self.message_status_callback(sent_messages[1], "nhsapp", "failed")
        self.message_status_callback(sent_messages[1], "sms", "sending")
        self.message_status_callback(sent_messages[1], "sms", "failed")
        self.message_status_callback(sent_messages[1], "letter", "sending")
        self.message_status_callback(sent_messages[1], "letter", "delivered")
        self.channel_status_callback(sent_messages[1], "nhsapp", "sending", "received")
        self.channel_status_callback(sent_messages[1], "nhsapp", "failed", "unnotified")
        self.channel_status_callback(sent_messages[1], "sms", "sending", "received")
        self.channel_status_callback(
            sent_messages[1], "sms", "failed", "permanent_failure"
        )
        self.channel_status_callback(sent_messages[1], "letter", "sending", "accepted")
        self.channel_status_callback(
            sent_messages[1], "letter", "delivered", "received"
        )

    def channel_status_callback(
        self, message, channel, channel_status, supplier_status
    ):
        self.make_callback_request(
            {
                "data": [
                    {
                        "type": "ChannelStatus",
                        "attributes": {
                            "messageId": str(message.notify_id),
                            "messageReference": str(message.id),
                            "cascadeType": "primary",
                            "cascadeOrder": 1,
                            "channel": channel,
                            "channelStatus": channel_status,
                            "channelStatusDescription": "Some words",
                            "channelFailureReasonCode": "Some code",
                            "supplierStatus": supplier_status,
                            "timestamp": datetime.now().isoformat(),
                            "retryCount": 1,
                        },
                        "links": {
                            "message": f"https://api.service.nhs.uk/comms/v1/messages/{message.notify_id}"
                        },
                        "meta": {
                            "idempotencyKey": "".join(
                                random.choices(
                                    string.ascii_letters + string.digits, k=63
                                )
                            )
                        },
                    }
                ]
            }
        )

    def message_status_callback(self, message, channel, status):
        self.make_callback_request(
            {
                "data": [
                    {
                        "type": "MessageStatus",
                        "attributes": {
                            "messageId": str(message.notify_id),
                            "messageReference": str(message.id),
                            "messageStatus": status,
                            "messageStatusDescription": "Some words",
                            "messageFailureReasonCode": "Some code",
                            "channels": [{"type": channel, "channelStatus": status}],
                            "timestamp": datetime.now().isoformat(),
                            "routingPlan": {
                                "id": "b838b13c-f98c-4def-93f0-515d4e4f4ee1",
                                "name": "Plan Abc",
                                "version": "ztoe2qRAM8M8vS0bqajhyEBcvXacrGPp",
                                "createdDate": "2023-11-17T14:27:51.413Z",
                            },
                        },
                        "links": {
                            "message": f"https://api.service.nhs.uk/comms/v1/messages/{message.notify_id}"
                        },
                        "meta": {
                            "idempotencyKey": "".join(
                                random.choices(
                                    string.ascii_letters + string.digits, k=63
                                )
                            )
                        },
                    }
                ]
            }
        )

    def make_callback_request(self, body):
        sig_key = f"{os.getenv('NHS_NOTIFY_APPLICATION_ID')}.{os.getenv('NHS_NOTIFY_API_KEY')}"
        signature = hmac.new(
            bytes(sig_key, "ASCII"),
            msg=bytes(json.dumps(body), "ASCII"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        headers = {
            "X-Api-Key": os.getenv("NHS_NOTIFY_API_KEY"),
            "X-HMAC-sha256-signature": signature,
        }

        response = self.client.post(
            "/notifications/message-status/create",
            body,
            enforce_csrf_checks=True,
            content_type="application/json",
            headers=headers,
        )
        assert response.status_code == 200
