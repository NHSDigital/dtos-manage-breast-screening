import os
from typing import Any

from azure.core.exceptions import ResourceExistsError
from azure.identity import ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings


class BlobStorage:
    def __init__(self):
        blob_mi_client_id = os.getenv("BLOB_MI_CLIENT_ID")
        storage_account_name = os.getenv("STORAGE_ACCOUNT_NAME")
        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")

        # We use Managed Identity credentials for deployed environments
        if blob_mi_client_id and storage_account_name:
            self.client = BlobServiceClient(
                f"https://{storage_account_name}.blob.core.windows.net",
                credential=ManagedIdentityCredential(client_id=blob_mi_client_id),
            )

        if connection_string:
            self.client = BlobServiceClient.from_connection_string(connection_string)

    def find_or_create_container(self, container_name: str) -> ContainerClient:
        """Find or create an Azure Storage Blob container"""
        try:
            return self.client.create_container(container_name)
        except ResourceExistsError:
            return self.client.get_container_client(container_name)

    def add(
        self,
        filename: str,
        content: str,
        container_name: str | None = None,
        content_encoding="ASCII",
        content_type="application/dat",
    ) -> dict[str, Any]:
        """Write a file to the configured blob container"""

        if not container_name:
            container_name = os.getenv("BLOB_CONTAINER_NAME")
        container = self.find_or_create_container(container_name)
        blob_client = container.get_blob_client(filename)
        return blob_client.upload_blob(
            content,
            blob_type="BlockBlob",
            content_settings=ContentSettings(
                content_type=content_type, content_encoding=content_encoding
            ),
            overwrite=True,
        )
