import asyncio
import base64
import hashlib
import hmac
import json
import urllib.parse
from unittest.mock import AsyncMock, Mock, patch

import pytest
from asgiref.sync import sync_to_async
from websockets.asyncio.client import ClientConnection

from manage_breast_screening.gateway.relay_service import (
    SAS_TOKEN_EXPIRY_SECONDS,
    RelayService,
    RelayURI,
)

from .factories import GatewayActionFactory, RelayFactory


class TestRelayService:
    @pytest.fixture
    def relay(self, db):
        """Create a relay synchronously for use in async tests."""
        return RelayFactory.create()

    @pytest.fixture
    def gateway_action(self, db):
        """Create a gateway action synchronously for use in async tests."""
        return GatewayActionFactory.create(
            payload={"action_id": "a1", "type": "test"},
        )

    def test_create_sas_token_deterministic(self):
        relay = RelayFactory.build()
        uri = RelayURI(relay)

        fixed_time = 1_700_000_000

        with patch("time.time", return_value=fixed_time):
            token = uri.create_sas_token()

        base_uri = f"https://{relay.namespace}/{relay.hybrid_connection_name}"
        encoded_uri = urllib.parse.quote_plus(base_uri)
        expiry = str(fixed_time + SAS_TOKEN_EXPIRY_SECONDS)

        expected_signature = base64.b64encode(
            hmac.new(
                relay.shared_access_key.encode(),
                f"{encoded_uri}\n{expiry}".encode(),
                hashlib.sha256,
            ).digest()
        )
        expected_signature = urllib.parse.quote_plus(expected_signature)

        expected = (
            f"SharedAccessSignature sr={encoded_uri}"
            f"&sig={expected_signature}"
            f"&se={expiry}&skn={relay.key_name}"
        )

        assert token == expected

    def test_connection_url_contains_token_and_action(self):
        relay = RelayFactory.build()
        uri = RelayURI(relay)

        with patch.object(RelayURI, "create_sas_token", return_value="TOKEN"):
            url = uri.connection_url()

        assert url.startswith(
            f"wss://{relay.namespace}/$hc/{relay.hybrid_connection_name}"
        )
        assert "sb-hc-action=connect" in url
        assert "sb-hc-token=TOKEN" in url

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_async_send_action_success(self, relay, gateway_action):
        subject = RelayService()

        mock_ws = AsyncMock(spec=ClientConnection)
        mock_ws.recv.return_value = json.dumps({"status": "created"})

        with patch.object(subject, "_get_connection", return_value=mock_ws):
            await subject.async_send_action(relay, gateway_action)

        mock_ws.send.assert_called_once_with(
            json.dumps({"action_id": "a1", "type": "test"})
        )

        await sync_to_async(gateway_action.refresh_from_db)()
        assert gateway_action.status == "confirmed"
        assert gateway_action.last_error == ""
        assert gateway_action.sent_at is not None
        assert gateway_action.confirmed_at is not None

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_send_action_timeout(self, relay, gateway_action):
        subject = RelayService()

        mock_ws = AsyncMock(spec=ClientConnection)
        mock_ws.recv.side_effect = asyncio.TimeoutError

        with patch.object(subject, "_get_connection", return_value=mock_ws):
            await subject.async_send_action(
                relay,
                gateway_action,
            )

        mock_ws.send.assert_called_once_with(
            json.dumps({"action_id": "a1", "type": "test"})
        )

        await sync_to_async(gateway_action.refresh_from_db)()
        assert gateway_action.status == "failed"
        assert "Timeout waiting for response" in gateway_action.last_error

    @pytest.mark.asyncio
    @pytest.mark.django_db(transaction=True)
    async def test_send_action_bad_response(self, relay, gateway_action):
        subject = RelayService()

        mock_ws = AsyncMock(spec=ClientConnection)
        mock_ws.recv.return_value = json.dumps({"unexpected": "data"})

        with patch.object(subject, "_get_connection", return_value=mock_ws):
            await subject.async_send_action(
                relay,
                gateway_action,
            )

        mock_ws.send.assert_called_once_with(
            json.dumps({"action_id": "a1", "type": "test"})
        )

        await sync_to_async(gateway_action.refresh_from_db)()
        assert gateway_action.status == "failed"
        assert "Unexpected response status from gateway" in gateway_action.last_error

    def test_sync_send_action(self, relay, gateway_action):
        subject = RelayService()

        with patch.object(
            asyncio,
            "run",
        ) as mock_asyncio_run:
            subject.sync_send_action(relay, gateway_action)

        assert mock_asyncio_run.call_count == 1
        coro = mock_asyncio_run.call_args[0][0]
        assert (
            mock_asyncio_run.call_args[0][0].__qualname__
            == "RelayService.async_send_action"
        )
        coro.close()

    def test_send_action_starts_new_thread(self, relay, gateway_action):
        subject = RelayService()

        mock_thread = Mock()

        with patch(
            f"{RelayService.__module__}.threading.Thread", return_value=mock_thread
        ) as mock_thread_class:
            new_thread = subject.send_action(relay, gateway_action)

        mock_thread_class.assert_called_once_with(
            target=subject.sync_send_action,
            args=(relay, gateway_action),
            daemon=True,
        )
        mock_thread.start.assert_called_once()
        assert new_thread is mock_thread

    @pytest.mark.asyncio
    async def test_connection_is_cached(self):
        relay = RelayFactory.build()
        manager = RelayService()

        fake_connection = AsyncMock()

        with patch.object(
            manager,
            "_create_connection",
            AsyncMock(return_value=fake_connection),
        ):
            conn1 = await manager._get_connection(relay)
            conn2 = await manager._get_connection(relay)

        assert conn1 is conn2
        assert relay.id in manager._connections
