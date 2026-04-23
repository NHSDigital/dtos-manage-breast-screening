import json
import logging
import os
from urllib.request import urlopen

import jwt
from django.conf import settings
from ninja.security import HttpBearer

logger = logging.getLogger(__name__)

ALLOWED_ALGORITHMS = ["RS256"]


class TokenValidator(HttpBearer):
    def authenticate(self, request, token) -> dict | None:
        if self.bypass_authentication:
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
            logger.exception("Unable to parse authentication token.")

    def _decode(self, token: str, rsa_key: dict) -> dict | None:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALLOWED_ALGORITHMS,
                audience=os.getenv("API_AUDIENCE"),
                issuer=f"https://sts.windows.net/{self.tenant_id}/",
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

    @property
    def discovery_keys_url(self) -> str:
        return f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"

    @property
    def tenant_id(self) -> str | None:
        return os.getenv("TENANT_ID", "")

    @property
    def bypass_authentication(self) -> bool:
        return getattr(settings, "BYPASS_API_TOKEN_AUTH", False)
