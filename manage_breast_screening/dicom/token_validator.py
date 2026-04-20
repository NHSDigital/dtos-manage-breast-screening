import json
import logging
import os
from urllib.request import urlopen

import jwt
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)

ALLOWED_ALGORITHMS = ["RS256"]


class TokenValidator(HttpBearer):
    def __init__(self):
        self.bypass_auth = os.getenv("BYPASS_API_TOKEN_AUTH", "false").lower() == "true"
        self.api_audience = os.getenv("API_AUDIENCE", "")
        self.tenant_id = os.getenv("TENANT_ID", "")
        self.discovery_keys_url = (
            "https://login.microsoftonline.com/"
            + self.tenant_id
            + "/discovery/v2.0/keys"
        )
        self.issuer_url = "https://sts.windows.net/" + self.tenant_id + "/"

    def authenticate(self, request, token) -> dict | None:
        if self.bypass_auth:
            logger.warning("Authentication bypass is enabled.")
            return {"sub": "bypass_user"}

        rsa_key = self._rsa_key(token)
        if rsa_key:
            return self._decode(token, rsa_key)

        logger.error("Unable to find appropriate key")

    def _rsa_key(self, token) -> dict | None:
        try:
            jsonurl = urlopen(self.discovery_keys_url)
            jwks = json.loads(jsonurl.read())
            unverified_header = jwt.get_unverified_header(token)
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    return {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"],
                    }
        except Exception:
            logger.error("Unable to parse authentication token.", exc_info=True)

    def _decode(self, token: str, rsa_key: dict) -> dict | None:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALLOWED_ALGORITHMS,
                audience=self.api_audience,
                issuer=self.issuer_url,
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.exception("Token is expired")
        except (jwt.InvalidAudienceError, jwt.InvalidIssuerError):
            logger.exception("Invalid claims. Please check the audience and issuer.")
        except jwt.InvalidTokenError:
            logger.exception("Token is invalid")
        except Exception:
            logger.exception("Unable to parse authentication token.")
