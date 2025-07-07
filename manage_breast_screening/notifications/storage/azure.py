"""
Azure Blob Storage utilities for the Notifications app

This module provides functions for interacting with Azure Blob Storage,
specifically for storing MESH messages and other notification data.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict

from azure.storage.blob import BlobServiceClient
from django.conf import settings

logger = logging.getLogger(__name__)


def get_azure_blob_client():
    """
    Create and return an Azure Blob Service Client

    Returns:
        BlobServiceClient: Configured Azure Blob Service Client

    Raises:
        ValueError: If Azure Storage connection string is not configured
    """
    # Get connection string from Django settings or environment variable
    connection_string = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)

    if not connection_string:
        # Fallback to environment variable
        connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

    if not connection_string:
        raise ValueError(
            "Azure Storage connection string not configured. "
            "Set AZURE_STORAGE_CONNECTION_STRING in settings or environment."
        )

    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        logger.debug("Successfully created Azure Blob Service Client")
        return blob_service_client
    except Exception as e:
        logger.error(
            "Failed to create Azure Blob Service Client",
            extra={"error": str(e), "error_type": type(e).__name__},
        )
        raise


def store_message_to_blob(
    blob_service_client: BlobServiceClient, message: Dict[str, Any]
) -> str:
    """
    Store a message to Azure Blob Storage with proper filename structure

    Args:
        blob_service_client: Azure Blob Service Client
        message: Dictionary containing message data with 'id', 'content', and 'bso_code'

    Returns:
        str: The blob path where the message was stored

    Raises:
        ValueError: If required message fields are missing
        Exception: If blob storage operation fails
    """
    if not message.get("id"):
        raise ValueError("Message ID is required")

    if "content" not in message:
        raise ValueError("Message content is required")

    # Get BSO code from message (should be extracted from filename)
    bso_code = message.get("bso_code", "UNK")

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    filename = f"{bso_code}_{timestamp}.dat"

    # Create date-based folder structure
    date_folder = datetime.now().strftime("%Y-%m-%d")
    blob_path = f"{date_folder}/{filename}"

    # Get container name from settings
    container_name = getattr(settings, "MESH_CONTAINER_NAME", "mesh-messages")

    try:
        # Get blob client for the specific file
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_path
        )

        # Prepare content for upload
        content = message["content"]
        if isinstance(content, str):
            content = content.encode("utf-8")

        # Upload the blob
        blob_client.upload_blob(content, overwrite=True)

        logger.info(
            "Successfully stored message to Azure Blob Storage",
            extra={
                "message_id": message["id"],
                "bso_code": bso_code,
                "blob_path": blob_path,
                "container": container_name,
                "content_size": len(content),
            },
        )

        return blob_path

    except Exception as e:
        logger.error(
            "Failed to store message to Azure Blob Storage",
            extra={
                "message_id": message["id"],
                "bso_code": bso_code,
                "blob_path": blob_path,
                "container": container_name,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise


def list_blobs_in_container(container_name: str = None, prefix: str = None) -> list:
    """
    List blobs in a container with optional prefix filtering

    Args:
        container_name: Name of the container (defaults to MESH_CONTAINER_NAME)
        prefix: Optional prefix to filter blobs

    Returns:
        list: List of blob names in the container
    """
    if container_name is None:
        container_name = getattr(settings, "MESH_CONTAINER_NAME", "mesh-messages")

    try:
        blob_service_client = get_azure_blob_client()
        container_client = blob_service_client.get_container_client(container_name)

        blobs = []
        for blob in container_client.list_blobs(name_starts_with=prefix):
            blobs.append(blob.name)

        logger.debug(
            f"Listed {len(blobs)} blobs in container {container_name}",
            extra={
                "container": container_name,
                "prefix": prefix,
                "blob_count": len(blobs),
            },
        )

        return blobs

    except Exception as e:
        logger.error(
            "Failed to list blobs in container",
            extra={
                "container": container_name,
                "prefix": prefix,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise


def delete_blob(blob_path: str, container_name: str = None) -> bool:
    """
    Delete a blob from Azure Blob Storage

    Args:
        blob_path: Path to the blob to delete
        container_name: Name of the container (defaults to MESH_CONTAINER_NAME)

    Returns:
        bool: True if deletion was successful

    Raises:
        Exception: If blob deletion fails
    """
    if container_name is None:
        container_name = getattr(settings, "MESH_CONTAINER_NAME", "mesh-messages")

    try:
        blob_service_client = get_azure_blob_client()
        blob_client = blob_service_client.get_blob_client(
            container=container_name, blob=blob_path
        )

        blob_client.delete_blob()

        logger.info(
            "Successfully deleted blob from Azure Blob Storage",
            extra={"blob_path": blob_path, "container": container_name},
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to delete blob from Azure Blob Storage",
            extra={
                "blob_path": blob_path,
                "container": container_name,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        raise
