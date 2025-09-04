import logging
from typing import Any, Dict

from authlib.jose import JoseError, jwt
from authlib.jose.errors import (
    ExpiredTokenError,
    InvalidClaimError,
    InvalidTokenError,
    MissingClaimError,
)

logger = logging.getLogger(__name__)


class InvalidLogoutToken(Exception):
    """Raised when a CIS2 back-channel logout token is invalid."""


class DecodeLogoutToken:
    def call(
        self,
        metadata: Dict[str, Any],
        logout_token: str,
        client_id: str,
        key_loader,
    ):
        """
        Decode and validate a CIS2 back-channel logout token.

        Returns the decoded claims on success and raises InvalidLogoutToken on
        any underlying decoding/validation error.
        """
        try:
            verification_rules = {
                "iss": {"values": [metadata["issuer"]], "essential": True},
                "aud": {"values": [client_id], "essential": True},
                "exp": {"essential": True},
                "iat": {"essential": True},
                "events": {
                    "essential": True,
                    "validate": lambda claim, value: isinstance(value, dict)
                    and "http://schemas.openid.net/event/backchannel-logout" in value,
                },
                "nonce": {"validate": lambda claim, value: value is None},
            }
            claims = jwt.decode(
                logout_token,
                key=key_loader,
                claims_options=verification_rules,
            )
            claims.validate(leeway=60)
            return claims
        except (
            ExpiredTokenError,
            InvalidClaimError,
            InvalidTokenError,
            JoseError,
            MissingClaimError,
        ) as e:
            logger.exception("Invalid logout token")
            raise InvalidLogoutToken() from e
