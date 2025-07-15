import os
from typing import Any

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient, ContainerClient, ContentSettings


class Helpers:
    def find_or_create_blob_container(self) -> ContainerClient:
        """Find or create an Azure Storage Blob container"""

        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("BLOB_CONTAINER_NAME")

        service_client = BlobServiceClient.from_connection_string(connection_string)

        try:
            return service_client.create_container(container_name)
        except ResourceExistsError:
            return service_client.get_container_client(container_name)

    def add_to_blob_storage(
        self,
        filename: str,
        content: str,
        content_encoding="ASCII",
        content_type="application/dat",
    ) -> dict[str, Any]:
        """Write a file to the configured blob container"""

        container = self.find_or_create_blob_container()
        blob_client = container.get_blob_client(filename)
        return blob_client.upload_blob(
            content,
            blob_type="BlockBlob",
            content_settings=ContentSettings(
                content_type=content_type, content_encoding=content_encoding
            ),
            overwrite=True,
        )
