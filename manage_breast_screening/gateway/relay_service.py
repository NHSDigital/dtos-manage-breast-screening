import asyncio
import base64
import hashlib
import hmac
import json
import logging
import time
import urllib.parse
from datetime import datetime, timezone

from websockets.asyncio.client import connect

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


class SendActionResult:
    def __init__(
        self,
        sent_at: datetime | None = None,
        confirmed_at: datetime | None = None,
        failed_at: datetime | None = None,
    ):
        self.sent_at = sent_at
        self.confirmed_at = confirmed_at
        self.failed_at = failed_at
        self.error = None
        self.status = GatewayActionStatus.PENDING

    def failed(self, msg: str):
        logger.error(msg)
        self.status = GatewayActionStatus.FAILED
        self.failed_at = datetime.now(timezone.utc)
        self.error = msg

    def sent(self, msg: str):
        logger.info(msg)
        self.status = GatewayActionStatus.SENT
        self.sent_at = datetime.now(timezone.utc)

    def confirmed(self, msg: str):
        logger.info(msg)
        self.status = GatewayActionStatus.CONFIRMED
        self.confirmed_at = datetime.now(timezone.utc)


class RelayService:
    def send_echo(self, relay: Relay):
        """Sends an echo message to the relay and logs the response."""
        try:
            relay_uri = RelayURI(relay)
            url = relay_uri.connection_url()
            logger.info(f"Connecting to relay {relay.id} at {url}")
            asyncio.run(self._async_send_echo(url, relay.id))
        except Exception as e:
            logger.error(f"Error sending echo to relay {relay.id}: {e}")

    async def _async_send_echo(self, url: str, relay_id: int):
        try:
            async with connect(
                url, compression=None, open_timeout=OPEN_CONNECTION_TIMEOUT_SECONDS
            ) as conn:
                echo_message = {
                    "action_type": "echo",
                    "timestamp": datetime.now().isoformat(),
                }
                await conn.send(json.dumps(echo_message))
                logger.info(f"Sent echo message to relay {relay_id}")

                response = await asyncio.wait_for(
                    conn.recv(), timeout=RECEIVE_TIMEOUT_SECONDS
                )
                logger.info(f"Received response from relay {relay_id}: {response}")

        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response from relay {relay_id}")

        except Exception as e:
            logger.error(f"Error during echo communication with relay {relay_id}: {e}")

    def send_action(self, relay: Relay, action: GatewayAction):
        """
        Synchronous wrapper around async_send_action.
        Updates the GatewayAction based on the eventloop outcome.
        """
        result = asyncio.run(self.async_send_action(relay, action))
        self.update_gateway_action(action, result)

    async def async_send_action(
        self, relay: Relay, action: GatewayAction
    ) -> SendActionResult:
        result = SendActionResult()

        try:
            relay_uri = RelayURI(relay)
            url = relay_uri.connection_url()
            async with connect(
                url, compression=None, open_timeout=OPEN_CONNECTION_TIMEOUT_SECONDS
            ) as conn:
                await conn.send(json.dumps(action.payload))
                result.sent(f"Sent action {action.id} to relay {relay.id}")

                response = await asyncio.wait_for(
                    conn.recv(), timeout=RECEIVE_TIMEOUT_SECONDS
                )
                response_data = json.loads(response)

                if response_data.get("status") in ("created", "processed"):
                    result.confirmed(f"Action {action.id} confirmed by gateway")
                else:
                    result.failed(
                        f"Unexpected response status from gateway: {response_data}"
                    )

        except asyncio.TimeoutError:
            result.failed(f"Timeout waiting for response from gateway {relay.id}")

        except Exception as e:
            result.failed(f"Error sending action to gateway {relay.id}: {e}")

        return result

    def update_gateway_action(self, action: GatewayAction, result: SendActionResult):
        """Update the GatewayAction based on the SendActionResult."""
        action.status = result.status
        if result.status == GatewayActionStatus.FAILED:
            action.last_error = result.error
            action.failed_at = result.failed_at
            action.save(update_fields=["status", "last_error"])
        elif result.status == GatewayActionStatus.SENT:
            action.sent_at = result.sent_at
            action.save(update_fields=["status", "sent_at"])
        elif result.status == GatewayActionStatus.CONFIRMED:
            action.sent_at = result.sent_at
            action.confirmed_at = result.confirmed_at
            action.save(update_fields=["status", "sent_at", "confirmed_at"])
