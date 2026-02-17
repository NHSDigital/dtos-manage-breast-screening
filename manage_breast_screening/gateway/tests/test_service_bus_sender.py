from unittest.mock import MagicMock, patch

import pytest

from manage_breast_screening.gateway.service_bus_sender import ServiceBusSender

from .factories import GatewayActionFactory


class TestServiceBusSender:
    @pytest.fixture
    def gateway_action(self, db):
        return GatewayActionFactory.create(
            payload={"action_id": "a1", "action_type": "worklist.create_item"},
        )

    @pytest.fixture
    def mock_service_bus(self):
        with patch(
            "manage_breast_screening.gateway.service_bus_sender.ServiceBusClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_sender = MagicMock()
            mock_client_class.from_connection_string.return_value.__enter__ = MagicMock(
                return_value=mock_client
            )
            mock_client_class.from_connection_string.return_value.__exit__ = MagicMock(
                return_value=False
            )
            mock_client.get_queue_sender.return_value.__enter__ = MagicMock(
                return_value=mock_sender
            )
            mock_client.get_queue_sender.return_value.__exit__ = MagicMock(
                return_value=False
            )
            yield mock_client_class, mock_sender

    @pytest.mark.django_db(transaction=True)
    def test_send_action_success(self, gateway_action, mock_service_bus):
        _, mock_sender = mock_service_bus

        subject = ServiceBusSender()
        subject.connection_string = "test-connection-string"

        assert subject.send_action(gateway_action) is True

        mock_sender.send_messages.assert_called_once()

        gateway_action.refresh_from_db()
        assert gateway_action.status == "sent"
        assert gateway_action.sent_at is not None

    @pytest.mark.django_db(transaction=True)
    def test_send_action_failure(self, gateway_action):
        with patch(
            "manage_breast_screening.gateway.service_bus_sender.ServiceBusClient"
        ) as mock_client_class:
            mock_client_class.from_connection_string.side_effect = Exception(
                "Connection failed"
            )

            subject = ServiceBusSender()
            subject.connection_string = "test-connection-string"

            result = subject.send_action(gateway_action)

            assert result is False

            gateway_action.refresh_from_db()
            assert gateway_action.status == "failed"
            assert "Connection failed" in gateway_action.last_error
