import asyncio
import base64
import hashlib
import hmac
import json
import logging
import threading
import time
import urllib.parse

from asgiref.sync import sync_to_async
from django import db
from websockets.asyncio.client import ClientConnection, connect

from .models import GatewayAction, GatewayActionStatus, Relay

logger = logging.getLogger(__name__)

SAS_TOKEN_EXPIRY_SECONDS = 3600
OPEN_CONNECTION_TIMEOUT_SECONDS = 30
RECEIVE_TIMEOUT_SECONDS = 30


class RelayURI:
    def __init__(self, relay: Relay):
        self.relay = relay

    def create_sas_token(self, expiry_seconds: int = SAS_TOKEN_EXPIRY_SECONDS) -> str:
        """Create SAS token for Azure Relay authentication."""
        uri = f"https://{self.relay.namespace}/{self.relay.hybrid_connection_name}"
        encoded_uri = urllib.parse.quote_plus(uri)
        expiry = str(int(time.time() + expiry_seconds))
        signature = base64.b64encode(
            hmac.new(
                self.relay.shared_access_key.encode(),
                f"{encoded_uri}\n{expiry}".encode(),
                hashlib.sha256,
            ).digest()
        )
        return (
            f"SharedAccessSignature sr={encoded_uri}"
            f"&sig={urllib.parse.quote_plus(signature)}"
            f"&se={expiry}&skn={self.relay.key_name}"
        )

    def connection_url(self) -> str:
        token = self.create_sas_token()
        return (
            f"wss://{self.relay.namespace}/$hc/{self.relay.hybrid_connection_name}"
            f"?sb-hc-action=connect&sb-hc-token={urllib.parse.quote_plus(token)}"
        )


class RelayService:
    def __init__(self):
        self._connections: dict[str, object] = {}

    def send_action(self, relay: Relay, action: GatewayAction) -> threading.Thread:
        """
        Send an action to a gateway in a daemon thread.

        Args:
            relay: The Relay used to connect to the Gateway application
            action: The GatewayAction containing the payload to send
        """
        thread = threading.Thread(
            target=self.sync_send_action, args=(relay, action), daemon=True
        )
        thread.start()
        return thread

    def sync_send_action(self, relay: Relay, action: GatewayAction):
        """
        Synchronous wrapper to send an action to a gateway.

        Args:
            relay: The Relay used to connect to the Gateway application
            action: The GatewayAction containing the payload to send
        """
        # Ensure database connections are not left open in threads
        asyncio.run(self.async_send_action(relay, action))
        db.connection.close()

    async def async_send_action(self, relay: Relay, action: GatewayAction):
        """
        Send an action to a gateway and wait for acknowledgment.

        Args:
            relay: The Relay used to connect to the Gateway application
            action: The GatewayAction containing the payload to send
        """
        try:
            conn = await self._get_connection(relay)
            if not conn:
                logger.error(f"Failed to get connection for relay {relay.id}")

            await conn.send(json.dumps(action.payload))
            await sync_to_async(action.update_status)(GatewayActionStatus.SENT)

            logger.info(f"Sent action {action.id} to relay {relay.id}")

            try:
                response = await asyncio.wait_for(
                    conn.recv(), timeout=RECEIVE_TIMEOUT_SECONDS
                )
                response_data = json.loads(response)

                if response_data.get("status") in ("created", "processed"):
                    logger.info(f"Action {action.id} confirmed by gateway")
                    await sync_to_async(action.update_status)(
                        GatewayActionStatus.CONFIRMED
                    )
                else:
                    warning_msg = (
                        f"Unexpected response status from gateway: {response_data}"
                    )
                    logger.warning(warning_msg)
                    await sync_to_async(action.mark_failed)(warning_msg)

            except asyncio.TimeoutError:
                error_msg = f"Timeout waiting for response from gateway {relay.id}"
                logger.error(error_msg)
                await sync_to_async(action.mark_failed)(error_msg)

        except Exception as e:
            error_msg = f"Error sending action to gateway {relay.id}: {e}"
            logger.error(error_msg)
            await sync_to_async(action.mark_failed)(error_msg)
            self._connections.pop(relay.id, None)

    async def _get_connection(self, relay: Relay) -> ClientConnection:
        if relay.id not in self._connections:
            self._connections[relay.id] = await self._create_connection(RelayURI(relay))
        return self._connections[relay.id]

    async def _create_connection(self, relay_uri: RelayURI) -> ClientConnection:
        url = relay_uri.connection_url()
        websocket = await connect(
            url, compression=None, open_timeout=OPEN_CONNECTION_TIMEOUT_SECONDS
        )
        logger.info(f"Created relay connection for relay {relay_uri.relay.id}")
        return websocket
