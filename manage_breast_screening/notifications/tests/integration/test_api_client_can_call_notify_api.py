import uuid
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.services.api_client import ApiClient
from manage_breast_screening.notifications.tests.factories import (
    MessageBatchFactory,
    MessageFactory,
)


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
@pytest.mark.integration
class TestApiClient:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "NHS_NOTIFY_API_MESSAGE_BATCH_URL", "http://localhost:8888/message/batch"
        )
        monkeypatch.setenv("API_OAUTH_TOKEN_URL", "http://localhost:8888/token")
        monkeypatch.setenv("API_OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("API_OAUTH_API_KID", "test-1")
        monkeypatch.setenv("API_OAUTH_PRIVATE_KEY", "test-key")

    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.mark.django_db
    def test_api_client_can_call_notify_api_and_verify_response(
        self, mock_jwt_encode, routing_plan_id
    ):
        message_1 = MessageFactory()
        message_2 = MessageFactory()
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)
        message_batch.messages.set([message_1, message_2])

        response = ApiClient().send_message_batch(message_batch)
        assert response.status_code == 201
