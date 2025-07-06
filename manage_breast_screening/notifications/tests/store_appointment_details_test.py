from datetime import datetime
from unittest import mock

from appointment_details import store_new_message


def test_store_new_message_uploads_blob_correctly():
    mock_blob_client = mock.Mock()
    message = {"id": "BSO_20250703T090102", "content": b"test file content"}

    today = datetime.now().strftime("%Y-%m-%d")
    expected_path = f"{today}/{message['id']}.dat"

    store_new_message(blob_client=mock_blob_client, message=message)

    mock_blob_client.get_blob_client.assert_called_with(expected_path)
    mock_blob_client.get_blob_client.return_value.upload_blob.assert_called_with(
        message["content"]
    )
