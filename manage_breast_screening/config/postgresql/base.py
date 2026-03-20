import logging
import time
from os import environ
from typing import cast

from azure.identity import ManagedIdentityCredential
from django.db.backends.postgresql import base

type AzureCredential = ManagedIdentityCredential | None

logger = logging.getLogger(__name__)


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

    ManagedIdentityCredential is used instead of DefaultAzureCredential to avoid
    probing the full credential chain on every cold start. DefaultAzureCredential
    tries EnvironmentCredential, WorkloadIdentityCredential, and others before
    reaching ManagedIdentityCredential; in Azure Container Apps some of those probes
    may make network calls before failing through. ManagedIdentityCredential goes
    directly to IMDS.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        client_id = environ.get("AZURE_DB_CLIENT_ID")
        self.azure_credential: AzureCredential = ManagedIdentityCredential(client_id=client_id) if client_id else None

    def _get_azure_connection_password(self) -> str:
        # Called by the psycopg3 connection pool when creating a new physical
        # connection, not on every request. The timing log below is therefore
        # expected to appear only at pool initialisation and when the pool expands.
        # https://docs.djangoproject.com/en/6.0/ref/databases/#connection-pool
        assert self.azure_credential is not None
        t0 = time.perf_counter()
        token = self.azure_credential.get_token(
            "https://ossrdbms-aad.database.windows.net/.default"
        ).token
        logger.debug("Azure DB token acquired in %.3fs", time.perf_counter() - t0)
        return token

    def get_connection_params(self) -> dict:  # type: ignore[override]
        params = cast(dict, super().get_connection_params())
        if params.get("host", "").endswith(".database.azure.com") and self.azure_credential:
            params["password"] = self._get_azure_connection_password()
        return params
