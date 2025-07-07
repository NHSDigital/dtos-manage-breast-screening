"""
MESH Inbox Polling Script for Django Notifications App

This script polls the MESH sandbox inbox and stores retrieved messages
in Azure Blob Storage with the filename format: yyyy-MM-dd/BSOCODE_TIMESTAMP.dat

The script is designed to be run within the Django environment and uses
Django settings for configuration.
"""

import logging
from typing import Dict, List

import requests
from django.conf import settings

from manage_breast_screening.notifications.storage.azure import (
    get_azure_blob_client,
    store_message_to_blob,
)

# Configure logging
logger = logging.getLogger(__name__)

# Configuration constants with Django settings fallbacks
MESH_BASE_URL = getattr(settings, "MESH_BASE_URL", "https://localhost:8700")
MAILBOX_ID = getattr(settings, "MESH_MAILBOX_ID", "X26ABC1")
REQUEST_TIMEOUT = getattr(settings, "MESH_REQUEST_TIMEOUT", 30)  # seconds


def get_mesh_inbox_messages() -> List[str]:
    """
    Retrieve list of message IDs from MESH sandbox inbox

    Returns:
        List of message IDs

    Raises:
        requests.RequestException: If API call fails
    """
    try:
        # MESH API endpoint for listing messages in inbox
        url = f"{MESH_BASE_URL}/messageexchange/{MAILBOX_ID}/inbox"

        logger.info(
            "Retrieving messages from MESH inbox",
            extra={"url": url, "mailbox_id": MAILBOX_ID, "timeout": REQUEST_TIMEOUT},
        )

        response = requests.get(
            url,
            verify=False,  # Disable SSL verification for local sandbox
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        # Parse response to extract message IDs
        # Note: Adjust parsing logic based on actual MESH API response format
        messages = response.json()
        message_ids = [msg.get("id") for msg in messages if msg.get("id")]

        logger.info(
            "Successfully retrieved messages from MESH inbox",
            extra={
                "message_count": len(message_ids),
                "mailbox_id": MAILBOX_ID,
                "url": url,
            },
        )
        return message_ids

    except requests.RequestException as e:
        logger.error(
            "Failed to retrieve MESH inbox messages",
            extra={
                "error": str(e),
                "mailbox_id": MAILBOX_ID,
                "url": url,
                "timeout": REQUEST_TIMEOUT,
            },
        )
        raise


def get_mesh_message_content(message_id: str) -> Dict:
    """
    Retrieve full message content for a specific message ID

    Args:
        message_id: The message ID to retrieve

    Returns:
        Dictionary containing message metadata and content

    Raises:
        requests.RequestException: If API call fails
    """
    try:
        # MESH API endpoint for retrieving specific message
        url = f"{MESH_BASE_URL}/messageexchange/{MAILBOX_ID}/inbox/{message_id}"

        logger.info(
            "Retrieving message content",
            extra={"message_id": message_id, "url": url, "timeout": REQUEST_TIMEOUT},
        )

        response = requests.get(
            url,
            verify=False,  # Disable SSL verification for local sandbox
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        # Parse response to extract message content and metadata
        # Note: Adjust parsing logic based on actual MESH API response format
        message_data = response.json()

        # Extract BSO code from filename (first three letters of the .dat filename)
        filename = message_data.get("filename", "")
        bso_code = filename[:3].upper() if filename and len(filename) >= 3 else "UNK"

        # Create message structure
        message = {
            "id": message_id,
            "content": message_data.get("content", b""),
            "filename": filename,
            "bso_code": bso_code,
            "metadata": message_data,
        }

        logger.info(
            "Successfully retrieved message content",
            extra={
                "message_id": message_id,
                "bso_code": bso_code,
                "mesh_filename": filename,
                "content_size": len(message.get("content", b"")),
            },
        )
        return message

    except requests.RequestException as e:
        logger.error(
            "Failed to retrieve message content",
            extra={
                "error": str(e),
                "message_id": message_id,
                "url": url,
                "timeout": REQUEST_TIMEOUT,
            },
        )
        raise


def run_mesh_polling():
    """
    Main function that orchestrates the end-to-end MESH polling and storage process

    This function can be called from Django management commands or scheduled tasks
    """
    logger.info(
        "Starting MESH inbox polling and storage process",
        extra={
            "mesh_base_url": MESH_BASE_URL,
            "mailbox_id": MAILBOX_ID,
            "container_name": getattr(settings, "MESH_CONTAINER_NAME", "mesh-messages"),
            "request_timeout": REQUEST_TIMEOUT,
        },
    )

    try:
        # Step 1: Connect to Azure Blob Storage using Django settings
        blob_service_client = get_azure_blob_client()

        # Step 2: Poll MESH inbox for message IDs
        message_ids = get_mesh_inbox_messages()

        if not message_ids:
            logger.info(
                "No messages found in MESH inbox", extra={"mailbox_id": MAILBOX_ID}
            )
            return

        # Step 3: Process each message
        successful_uploads = 0
        failed_uploads = 0

        for message_id in message_ids:
            try:
                message = get_mesh_message_content(message_id)

                store_message_to_blob(blob_service_client, message)
                successful_uploads += 1

            except Exception as e:
                logger.error(
                    "Failed to process message",
                    extra={
                        "error": str(e),
                        "message_id": message_id,
                        "successful_uploads": successful_uploads,
                        "failed_uploads": failed_uploads,
                    },
                )
                failed_uploads += 1
                continue

        logger.info(
            "MESH polling process completed",
            extra={
                "successful_uploads": successful_uploads,
                "failed_uploads": failed_uploads,
                "total_messages": len(message_ids),
                "mailbox_id": MAILBOX_ID,
            },
        )

    except Exception as e:
        logger.error(
            "Unexpected error in MESH polling process",
            extra={
                "error": str(e),
                "mailbox_id": MAILBOX_ID,
                "mesh_base_url": MESH_BASE_URL,
            },
        )
        raise


if __name__ == "__main__":
    # Allow running as standalone script for testing
    import os

    import django

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "manage_breast_screening.config.settings"
    )
    django.setup()

    run_mesh_polling()
