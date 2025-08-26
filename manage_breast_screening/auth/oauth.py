from authlib.integrations.django_client import OAuth
from authlib.jose import JsonWebKey
from authlib.oauth2.rfc7523 import PrivateKeyJWT
from cryptography.hazmat.primitives import serialization
from django.conf import settings

oauth = OAuth()


def get_cis2_client():
    """Return CIS2 OAuth client configured for private_key_jwt."""
    cfg = {
        "client_id": settings.CIS2_CLIENT_ID,
        "client_secret": settings.CIS2_PRIVATE_KEY,
        "server_metadata_url": settings.CIS2_SERVER_METADATA_URL,
        "client_kwargs": {"scope": settings.CIS2_SCOPES},
        "token_endpoint_auth_method": "private_key_jwt",
    }
    oauth.register(name="cis2", **cfg)
    client = oauth.create_client("cis2")
    metadata = getattr(client, "server_metadata", None) or {}
    token_endpoint = metadata.get("token_endpoint")
    if token_endpoint:
        try:
            headers = {}
            jwk = jwk_from_private_key()
            kid = jwk.thumbprint() if jwk else None
            if kid:
                headers["kid"] = kid
            client.register_client_auth_method(
                PrivateKeyJWT(token_endpoint, headers=headers or None)
            )
        except Exception:
            # If already registered or client doesn't support this method, ignore
            pass
    return client


def jwk_from_private_key():
    """Build a public JWK from the configured private key PEM (RSA-only).

    Returns:
        JsonWebKey | None: Public JWK or None on failure.
    """
    pem = getattr(settings, "CIS2_PRIVATE_KEY", None)
    if not pem:
        return None
    try:
        private_key = serialization.load_pem_private_key(
            pem.encode("utf-8"), password=None
        )
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return JsonWebKey.import_key(public_pem, {"kty": "RSA"})
    except Exception:
        return None
