from os import environ

from azure.identity import DefaultAzureCredential
from django.db.backends.postgresql import base


class DatabaseWrapper(base.DatabaseWrapper):
    """
    Wrap the Postgres engine to support Azure passwordless login
    https://learn.microsoft.com/en-us/azure/developer/intro/passwordless-overview

    This involves fetching a token at runtime to use as the database password.

    The consequence of this is our database credentials aren't static - they
    expire. We therefore need to ensure that every new connection
    checks the expiry date, and fetches a new one if necessary.

    Unless you disable persistent connections, each thread will maintain its own
    connection.
    Since Django 5.1 it is possible to configure a connection pool
    instead of using persistent connections, but that would require us to
    fix the credentials.
    See https://docs.djangoproject.com/en/5.2/ref/databases/#persistent-connections
    for more details of how this works.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.azure_credential = DefaultAzureCredential(
            managed_identity_client_id=environ.get("AZURE_CLIENT_ID")
        )

    def _get_azure_connection_password(self) -> str:
        # This makes use of in-memory token caching
        # https://github.com/Azure/azure-sdk-for-python/blob/main/sdk/identity/azure-identity/TOKEN_CACHING.md#in-memory-token-caching
        return self.azure_credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        ).token

    def get_connection_params(self) -> dict:
        params = super().get_connection_params()
        if params.get("host", "").endswith(".database.azure.com"):
            params["password"] = self._get_azure_connection_password()
        return params
