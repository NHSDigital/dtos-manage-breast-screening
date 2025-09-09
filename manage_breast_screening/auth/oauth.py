import logging
from urllib.parse import parse_qs

from authlib.integrations.django_client import OAuth
from authlib.jose import JsonWebKey
from authlib.oauth2.rfc7523 import PrivateKeyJWT, private_key_jwt_sign
from django.conf import settings
from django.urls import reverse

oauth = OAuth()


def get_cis2_client():
    """Return CIS2 OAuth client configured for private_key_jwt."""
    missing = [
        name
        for name in [
            "CIS2_CLIENT_ID",
            "CIS2_CLIENT_PRIVATE_KEY",
            "CIS2_CLIENT_PUBLIC_KEY",
            "CIS2_SERVER_METADATA_URL",
        ]
        if not getattr(settings, name, None)
    ]
    if missing:
        raise ValueError(f"Missing required CIS2 OAuth settings: {', '.join(missing)}")

    # Return existing client if already registered
    client = oauth._clients.get("cis2")
    if client:
        return client

    jwk = jwk_from_public_key()
    kid = jwk.thumbprint()

    client = oauth.register(
        "cis2",
        client_id=settings.CIS2_CLIENT_ID,
        client_secret=settings.CIS2_CLIENT_PRIVATE_KEY,
        server_metadata_url=settings.CIS2_SERVER_METADATA_URL,
        client_kwargs={
            "scope": settings.CIS2_SCOPES,
            "token_endpoint_auth_method": "private_key_jwt",
            # Add a DEBUG-only hook to log OIDC requests and responses
            "hooks": {"response": [_log_response]},
        },
        client_auth_methods=[CustomPrivateKeyJWT(headers={"kid": kid})],
    )

    return client


def cis2_redirect_uri():
    """Return the redirect URI for the CIS2 callback."""
    # Handle trailing slashes
    base_url = settings.BASE_URL.rstrip("/") if settings.BASE_URL else ""
    callback_path = reverse("auth:cis2_callback").rstrip("/")
    return f"{base_url}{callback_path}"


# Authlib's PrivateKeyJWT doesn't allow us to change the default exp value set in the JWT, so we
# define a custom class to do this.
class CustomPrivateKeyJWT(PrivateKeyJWT):
    def __init__(self, *, headers=None, alg="RS512", expires_in=300):
        super().__init__(headers=headers, alg=alg)
        self.expires_in = expires_in

    def sign(self, auth, token_endpoint):
        return private_key_jwt_sign(
            auth.client_secret,
            client_id=auth.client_id,
            token_endpoint=token_endpoint,
            header=self.headers,
            alg=self.alg,
            expires_in=self.expires_in,
        )


def jwk_from_public_key():
    """Build a public JWK from the configured public key PEM (RSA-only).

    Returns:
        JsonWebKey | None: Public JWK or None on failure.
    """
    jwk = JsonWebKey.import_key(settings.CIS2_CLIENT_PUBLIC_KEY, {"kty": "RSA"})
    return jwk


def _log_response(resp, *args, **kwargs):
    """Requests response hook: log request/response, with added formatting/spacing.

    WARNING: No redaction; intended for development diagnostics only. Set
    DEBUG=True in settings to enable.
    """
    if not settings.DEBUG:
        return

    logger = logging.getLogger("authlib")
    req = resp.request

    # Request body (safe decode)
    try:
        req_body = req.body
        if isinstance(req_body, (bytes, bytearray)):
            req_body = req_body.decode(errors="replace")
    except Exception:
        req_body = "<un-decodable>"

    # Parse x-www-form-urlencoded for readability
    parsed = None
    content_type = (req.headers or {}).get("Content-Type", "")
    if "application/x-www-form-urlencoded" in content_type and isinstance(
        req_body, str
    ):
        try:
            parsed = parse_qs(req_body)
        except Exception:
            parsed = None

    # Response body (truncate)
    try:
        resp_text = resp.text[:5000]
    except Exception:
        resp_text = "<unavailable>"

    # Build a single, spaced block to avoid multiple log lines interleaving
    sep = "=" * 80
    lines = [
        "",
        sep,
        f"HTTP {req.method} {req.url}",
        "",
        "-- Request --",
        f"Headers: {dict(req.headers or {})}",
    ]
    if parsed is not None:
        lines.append(f"Form: {parsed}")
    else:
        lines.append(f"Body: {req_body}")
    lines.extend(
        [
            "",
            "-- Response --",
            f"Status: {resp.status_code}",
            f"Headers: {dict(resp.headers or {})}",
            f"Body: {resp_text}",
            sep,
            "",
        ]
    )

    logger.debug("\n".join(lines))
