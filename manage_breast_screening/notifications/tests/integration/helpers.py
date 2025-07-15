from azure.blob.storage import BlobServiceClient, ContainerClient
from azure.core.exceptions import ResourceExistsError
import os


class Helpers:
    def find_or_create_blob_container(self) -> ContainerClient:
        """Find or create an Azure Storage Blob container"""

        connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
        container_name = os.getenv("BLOB_CONTAINER_NAME")

        service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        try:
            return service_client.create_container(container_name)
        except ResourceExistsError:
            return service_client.get_container_client(container_name)
