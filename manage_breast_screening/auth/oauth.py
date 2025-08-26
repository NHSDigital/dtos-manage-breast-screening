from authlib.integrations.django_client import OAuth
from authlib.jose import JsonWebKey
from authlib.oauth2.rfc7523 import PrivateKeyJWT, private_key_jwt_sign
from django.conf import settings

oauth = OAuth()


def get_cis2_client():
    """Return CIS2 OAuth client configured for private_key_jwt."""
    missing = [
        name
        for name in [
            "CIS2_CLIENT_ID",
            "CIS2_PRIVATE_KEY",
            "CIS2_PUBLIC_KEY",
            "CIS2_SERVER_METADATA_URL",
        ]
        if not getattr(settings, name, None)
    ]
    if missing:
        raise ValueError(f"Missing required CIS2 OAuth settings: {', '.join(missing)}")

    jwk = jwk_from_public_key()
    kid = jwk.thumbprint()

    client = oauth.register(
        "cis2",
        client_id=settings.CIS2_CLIENT_ID,
        client_secret=settings.CIS2_PRIVATE_KEY,
        server_metadata_url=settings.CIS2_SERVER_METADATA_URL,
        client_kwargs={
            "scope": settings.CIS2_SCOPES,
            "token_endpoint_auth_method": "private_key_jwt",
        },
        client_auth_methods=[CustomPrivateKeyJWT(headers={"kid": kid})],
    )

    return client


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
    jwk = JsonWebKey.import_key(settings.CIS2_PUBLIC_KEY, {"kty": "RSA"})
    return jwk
