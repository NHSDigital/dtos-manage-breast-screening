from os import environ

from azure.identity import DefaultAzureCredential
from storages.backends.azure_storage import AzureStorage


class ManagedIdentityAzureStorage(AzureStorage):
    def __init__(self, **kwargs):
        kwargs.setdefault(
            "token_credential",
            DefaultAzureCredential(managed_identity_client_id=environ.get("BLOB_MI_CLIENT_ID")),
        )
        super().__init__(**kwargs)
