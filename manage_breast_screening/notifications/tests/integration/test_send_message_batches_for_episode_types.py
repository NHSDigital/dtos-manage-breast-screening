import datetime
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.management.commands.helpers.routing_plan import (
    RoutingPlan,
)
from manage_breast_screening.notifications.management.commands.send_message_batch import (
    TZ_INFO,
    Command,
)
from manage_breast_screening.notifications.models import (
    Appointment,
    Message,
    MessageBatchStatusChoices,
)
from manage_breast_screening.notifications.tests.factories import AppointmentFactory


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
@pytest.mark.integration
class TestSendMessageBatch:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )
        monkeypatch.setenv("OAUTH_TOKEN_URL", "http://localhost:8888/token")
        monkeypatch.setenv("OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("OAUTH_API_KID", "test-1")
        monkeypatch.setenv("PRIVATE_KEY", "test-key")

    @pytest.mark.django_db
    def test_message_batch_is_sent_for_all_routing_plans(
        self, mock_jwt_encode, monkeypatch
    ):
        for routing_plan in RoutingPlan.all():
            for episode_type in routing_plan.episode_types:
                AppointmentFactory(
                    starts_at=datetime.datetime.now(tz=TZ_INFO),
                    episode_type=episode_type,
                    status="B",
                )

        Command().handle()

        for routing_plan in RoutingPlan.all():
            for episode_type in routing_plan.episode_types:
                appointment = Appointment.objects.filter(
                    episode_type=episode_type
                ).first()
                message = Message.objects.filter(appointment=appointment).first()
                assert message.batch.status == MessageBatchStatusChoices.SENT.value
