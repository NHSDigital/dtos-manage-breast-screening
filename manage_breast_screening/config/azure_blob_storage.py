from os import environ

from azure.identity import DefaultAzureCredential
from storages.backends.azure_storage import AzureStorage


class ManagedIdentityAzureStorage(AzureStorage):
    """
    AzureStorage subclass that instantiates DefaultAzureCredential in __init__
    rather than at settings import time, avoiding credential chain errors during
    Django startup before the managed identity is available.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault(
            "token_credential",
            DefaultAzureCredential(managed_identity_client_id=environ.get("BLOB_MI_CLIENT_ID")),
        )
        super().__init__(**kwargs)
