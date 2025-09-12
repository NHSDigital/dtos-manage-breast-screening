## Overview

Care Identity Service 2 (CIS2) is the NHS's identity and authentication service that provides secure access to NHS systems. This project integrates with CIS2 using OAuth 2.0 and OpenID Connect to authenticate NHS users.

Our implementation uses the `private_key_jwt` client authentication method, where we authenticate to CIS2 using a signed JWT instead of a traditional client secret. This provides enhanced security and is the recommended approach for NHS applications.

## Client Implementation

### Core Components

The CIS2 client is implemented in `manage_breast_screening/auth/oauth.py` using the Authlib library:

- **`get_cis2_client()`** - Returns a configured OAuth client for CIS2
- **`CustomPrivateKeyJWT`** - Custom JWT signing class that allows configurable expiration times
- **`jwk_from_public_key()`** - Converts our public key PEM to a JSON Web Key format

### Authentication Flow

The complete authentication process is in `manage_breast_screening/auth/views.py`:

1. **`cis2_sign_in()`** - Initiates OAuth flow
2. **`cis2_callback()`** - Handles CIS2 callback with these steps:
   - Exchanges authorization code for tokens
   - Retrieves user info from CIS2
   - Creates or updates Django user based on CIS2 user uid and profile
   - Logs the user into the Django session

### Private Key JWT

At the token request stage of the authentication flow, the client authenticates using private key JWT:

1. Creates a JWT signed with our private key
2. Includes the key ID (thumbprint of our public key) in the JWT header
3. Sends this JWT to CIS2's token endpoint for authentication
4. CIS2 validates the JWT using our published public key (see [JWKS Endpoint](#jwks-endpoint))

### MBS configuration

The following settings in `manage_breast_screening/config/settings.py` provide the basic configuration details needed by the CIS2 client:

- **`CIS2_SERVER_METADATA_URL`** - URL to CIS2's OpenID Connect discovery document
- **`CIS2_CLIENT_ID`** - Client identifier registered with CIS2
- **`CIS2_CLIENT_PRIVATE_KEY`** - RSA private key in PEM format for JWT signing (supports `\n` escaped newlines)
- **`CIS2_CLIENT_PUBLIC_KEY`** - Corresponding RSA public key in PEM format (supports `\n` escaped newlines)
- **`CIS2_SCOPES`** - OAuth scopes requested
- **`BASE_URL`** - Base URL for building absolute URLs (specifically for OAuth callbacks)

The private and public keys form a keypair used for the `private_key_jwt` client authentication method.

### CIS2 Environment Configuration

The CIS2 environment is configured via a connection manager. The INT environment manager, for example, can be found at:
https://connectionmanager.nhsint.auth-ptl.cis2.spineservices.nhs.uk/docs

Developers can authenticate with the connection manager by:

1. Clicking the green Authorize button
2. Entering a shared secret in the format "SecretAuth paste-secret-here"

Ask a team member for the shared secret.

Examples of configuration values handled by the connection manager:

```json
{
    "redirect_uris": [
      "https://relying-party.test/cis2_redirect"
    ],
    "backchannel_logout_uri": "https://relying-party.test/back-channel-logout",
    "token_endpoint_auth_method": "private_key_jwt",
    "jwks_uri": "https://relying-party.test/oidc/jwks_uri",
    "jwks_uri_signing_algorithm": "RS512"
}
```

## JWKS Endpoint

We implement a JSON Web Key Set (JWKS) endpoint at `/auth/cis2/jwks_uri` that publishes our public key. This allows CIS2 to verify the JWT signatures we send during authentication.

The endpoint returns a JSON response containing:

- Our RSA public key in JWK format
- Key ID (thumbprint)
- Usage indicator (`"use": "sig"`)
- Algorithm (`"alg": "RS512"`)

The [CIS2 Connection Manager](#cis2-environment-configuration) must be configured with the JWKS endpoint URL and the signing algorithm used (`RS512` in our case).

## Development Tips

### Debug Mode

To enable detailed logging of CIS2 OAuth requests and responses, set `DEBUG=True` in your environment configuration. This activates a response hook in the OAuth client that logs:

- Full HTTP request details (method, URL, headers, body)
- Complete response information (status, headers, body)
- Form-encoded request bodies are parsed for readability

**Warning**: Debug logging includes sensitive authentication data and should only be used in development environments.

### Making changes to the JWKS endpoint

The JWKS uri configured in the connection manager must be publicly accessible. When developing changes to it, a quick/useful approach is to use the URI of a public Github Gist containing the raw JSON outputted by your local `/auth/cis2/jwks_uri` endpoint.

### Debugging / making changes to the JWT

The JWT sent to CIS2 can be retrieved in local dev by inspecting debug log output and looking for requests to the CIS2 token endpoint.
The param named `client_assertion` contains the JWT payload.

The token can then be decoded and verified using a JWT decoder such as https://jwt.davetonge.co.uk/ , which also supports fetching the JWKS from a public URL.

## Useful links

- [CIS2 docs outlining the auth flow](https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/authorization-code-flow)
- [CIS2 docs detailing the various scopes and claims available](https://digital.nhs.uk/services/care-identity-service/applications-and-services/cis2-authentication/guidance-for-developers/detailed-guidance/scopes-and-claims)
