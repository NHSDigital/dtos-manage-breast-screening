from datetime import datetime


def store_new_message(blob_client, message):
    """
    Store message content to Azure Blob Storage with new filename structure

    Args:
        blob_client: Azure Blob Service Client
        message: Dictionary containing message data with 'id' and 'content' keys
    """
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    # Extract BSO code from message ID (first three letters)
    message_id = message.get("id", "")
    bso_code = message_id[:3].upper() if message_id else "UNK"

    # Create blob path with new format: yyyy-MM-dd/BSOCODE_TIMESTAMP.dat
    today = datetime.now().strftime("%Y-%m-%d")
    blob_name = f"{today}/{bso_code}_{timestamp}.dat"

    # Get blob client and upload content
    blob_client.get_blob_client(blob_name).upload_blob(message["content"])
