import uuid
from unittest.mock import patch

import pytest
import requests_mock

from manage_breast_screening.notifications.services.api_client import (
    ApiClient,
    OAuthError,
)
from manage_breast_screening.notifications.tests.factories import (
    MessageBatchFactory,
    MessageFactory,
)


@patch("manage_breast_screening.notifications.services.api_client.jwt.encode")
class TestApiClient:
    @pytest.fixture
    def routing_plan_id(self):
        return str(uuid.uuid4())

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        monkeypatch.setenv(
            "API_MESSAGE_BATCH_URL", "http://api.example.com/message/batch"
        )
        monkeypatch.setenv("OAUTH_TOKEN_URL", "http://oauth.example.com/token")
        monkeypatch.setenv("OAUTH_API_KEY", "a1b2c3d4")
        monkeypatch.setenv("OAUTH_API_KID", "test-1")
        monkeypatch.setenv("PRIVATE_KEY", "test-key")
        monkeypatch.setenv("CMAPI_CONSUMER_KEY", "consumer-key")

    @pytest.mark.django_db
    def test_send_message_batch(self, mock_jwt_encode, routing_plan_id):
        """Test a successful message batch request"""
        message_1 = MessageFactory()
        message_2 = MessageFactory()
        message_batch = MessageBatchFactory(routing_plan_id=routing_plan_id)
        message_batch.messages.set([message_1, message_2])

        with requests_mock.Mocker() as rm:
            rm.post(
                "http://oauth.example.com/token",
                json={"access_token": "000111"},
                status_code=200,
            )
            adapter = rm.post(
                "http://api.example.com/message/batch", json={}, status_code=201
            )

            response = ApiClient().send_message_batch(message_batch)

            request = adapter.last_request
            attributes = request.json()["data"]["attributes"]

            assert response.status_code == 201
            assert request.headers["Authorization"] == "Bearer 000111"
            assert request.headers["Content-Type"] == "application/vnd.api+json"
            assert request.headers["Accept"] == "application/vnd.api+json"
            assert request.headers["X-Consumer-Key"] == "consumer-key"

            assert attributes["messageBatchReference"] == str(message_batch.id)
            assert attributes["routingPlanId"] == message_batch.routing_plan_id
            assert attributes["messages"][0]["messageReference"] == str(message_1.id)
            assert (
                attributes["messages"][0]["recipient"]["nhsNumber"]
                == message_1.appointment.nhs_number
            )
            assert attributes["messages"][1]["messageReference"] == str(message_2.id)
            assert (
                attributes["messages"][1]["recipient"]["nhsNumber"]
                == message_2.appointment.nhs_number
            )

    @pytest.mark.django_db
    def test_send_message_batch_with_bad_request(
        self, mock_jwt_encode, routing_plan_id
    ):
        """Test for a 400 Bad Request response when sending a message batch"""
        message_batch = MessageBatchFactory.build()

        with requests_mock.Mocker() as rm:
            rm.post(
                "http://oauth.example.com/token",
                json={"access_token": "000111"},
                status_code=200,
            )
            rm.post(
                "http://api.example.com/message/batch",
                text="Bad Request",
                status_code=400,
            )

            response = ApiClient().send_message_batch(message_batch)

            assert response.status_code == 400

    def test_send_message_batch_with_auth_error(self, mock_jwt_encode):
        """Test for a 403 Forbidden response from the OAuth token provider"""
        message_batch = MessageBatchFactory.build()

        with requests_mock.Mocker() as rm:
            rm.post("http://oauth.example.com/token", text="Forbidden", status_code=403)
            adapter = rm.post(
                "http://api.example.com/message/batch", json={}, status_code=201
            )

            with pytest.raises(OAuthError):
                ApiClient().send_message_batch(message_batch)

            assert adapter.call_count == 0
