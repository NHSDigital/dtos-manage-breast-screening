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
    expire after ~1 hour. We therefore need to fetch a fresh token for every
    new connection. get_connection_params() is overridden to do this.

    We use persistent connections (CONN_MAX_AGE=180) so Django reuses each
    connection for up to 3 minutes and then closes it. This ensures tokens are
    always fresh (connections are recycled well before the ~1 hour token TTL)
    and keeps connections alive within Azure's NAT idle timeout (~4 minutes).
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
        # Called by get_connection_params() whenever Django opens a new connection.
        # With CONN_MAX_AGE=180, connections are reused for up to 3 minutes, so
        # this is called once per worker at startup and again every ~3 minutes —
        # never on every request.
        if self.azure_credential is None:
            raise RuntimeError(
                "Azure credential is not configured but an Azure DB host was detected. "
                "Ensure AZURE_DB_CLIENT_ID is set."
            )
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
