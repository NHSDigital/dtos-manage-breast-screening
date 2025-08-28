import os
from functools import cached_property
from typing import Any

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings


class BlobStorage:
    @cached_property
    def service_client(self) -> BlobServiceClient:
        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        return BlobServiceClient.from_connection_string(connection_string)

    def find_or_create_container(self, container_name: str) -> ContainerClient:
        """Find or create an Azure Storage Blob container"""
        try:
            return self.service_client.create_container(container_name)
        except ResourceExistsError:
            return self.service_client.get_container_client(container_name)

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
