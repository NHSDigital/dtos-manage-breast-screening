import os
import time
import uuid

import jwt
import requests

from manage_breast_screening.notifications.models import MessageBatch
from manage_breast_screening.notifications.presenters.message_batch_presenter import (
    MessageBatchPresenter,
)

EXPIRES_IN_MINUTES = 5

AUTHORIZATION_HEADER_NAME = "authorization"
SANDBOX_URL = "https://sandbox.api.service.nhs.uk/comms"


class OAuthError(Exception):
    pass


class ApiClient:
    def send_message_batch(self, message_batch: MessageBatch) -> requests.Response:
        response = requests.post(
            os.getenv("NHS_NOTIFY_API_MESSAGE_BATCH_URL"),
            headers=self.headers(),
            json=MessageBatchPresenter(message_batch).present(),
            timeout=10,
        )

        return response

    def headers(self) -> dict:
        return {
            "content-type": "application/vnd.api+json",
            "accept": "application/vnd.api+json",
            "x-correlation-id": str(uuid.uuid4()),
            AUTHORIZATION_HEADER_NAME: f"Bearer {self.bearer_token()}",
        }

    def bearer_token(self) -> str:
        if os.getenv("NHS_NOTIFY_API_MESSAGE_BATCH_URL", "").startswith(SANDBOX_URL):
            return "token"

        auth_jwt = jwt.encode(
            {
                "sub": os.getenv("API_OAUTH_API_KEY"),
                "iss": os.getenv("API_OAUTH_API_KEY"),
                "jti": str(uuid.uuid4()),
                "aud": os.getenv("API_OAUTH_TOKEN_URL"),
                "exp": int(time.time()) + (EXPIRES_IN_MINUTES * 60),
            },
            os.getenv("API_OAUTH_PRIVATE_KEY"),
            "RS512",
            {"alg": "RS512", "typ": "JWT", "kid": os.getenv("API_OAUTH_API_KID")},
        )

        response = requests.post(
            os.getenv("API_OAUTH_TOKEN_URL"),
            data={
                "grant_type": "client_credentials",
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": auth_jwt,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )

        if response.status_code != 200:
            raise OAuthError(response.text)

        return response.json()["access_token"]
