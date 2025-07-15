import uuid
from unittest.mock import patch

import pytest

from manage_breast_screening.notifications.api_client import ApiClient
from manage_breast_screening.notifications.factories import (
    MessageBatchFactory,
    MessageFactory,
)


@patch("notifications.api_client.jwt.encode")
class TestApiClient:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "API_MESSAGE_BATCH_URL", "http://cmapi_stub:8888/message/batches"
        )
        monkeypatch.setenv("OAUTH_TOKEN_URL", "http://cmapi_stub:8888/token")
        monkeypatch.setenv("OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("OAUTH_API_KID", "test-1")
        monkeypatch.setenv("PRIVATE_KEY", "test-key")

    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.mark.django_db
    def test_api_client_can_call_cmapi_and_verify_response(
        self, mock_jwt_encode, routing_plan_id
    ):
        message_1 = MessageFactory()
        message_2 = MessageFactory()
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)
        message_batch.messages.set([message_1, message_2])

        response = ApiClient().send_message_batch(message_batch)
        assert response.status_code == 201
