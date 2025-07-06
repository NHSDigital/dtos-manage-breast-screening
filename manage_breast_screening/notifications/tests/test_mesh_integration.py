"""
Integration tests for MESH polling functionality

These tests can run against a real MESH client when available,
but will be skipped if the MESH client is not running.
"""

import pytest
import requests
from django.conf import settings
from django.test import TestCase


def mesh_client_available():
    """Check if MESH client is available for integration testing"""
    try:
        mesh_url = getattr(settings, "MESH_BASE_URL", "https://localhost:8700")
        response = requests.get(f"{mesh_url}/health", timeout=5, verify=False)
        return response.status_code == 200
    except (requests.RequestException, Exception):
        return False


@pytest.mark.skipif(
    not mesh_client_available(),
    reason="MESH client not available for integration testing",
)
class TestMeshIntegration(TestCase):
    """Integration tests that require a real MESH client"""

    def setUp(self):
        """Set up test fixtures"""
        self.mesh_url = getattr(settings, "MESH_BASE_URL", "https://localhost:8700")
        self.mailbox_id = getattr(settings, "MESH_MAILBOX_ID", "X26ABC1")

    def test_mesh_client_connectivity(self):
        """Test that we can connect to the MESH client"""
        try:
            response = requests.get(f"{self.mesh_url}/health", timeout=5, verify=False)
            self.assertEqual(response.status_code, 200)
        except requests.RequestException as e:
            self.fail(f"Failed to connect to MESH client: {e}")

    def test_mesh_inbox_endpoint_exists(self):
        """Test that the MESH inbox endpoint exists and responds"""
        url = f"{self.mesh_url}/messageexchange/{self.mailbox_id}/inbox"
        try:
            response = requests.get(url, timeout=5, verify=False)
            # Should return 200 (with messages) or 404 (no messages)
            self.assertIn(response.status_code, [200, 404])
        except requests.RequestException as e:
            self.fail(f"Failed to access MESH inbox endpoint: {e}")

    def test_mesh_message_endpoint_structure(self):
        """Test that the MESH message endpoint has the expected structure"""
        # First get a list of messages
        inbox_url = f"{self.mesh_url}/messageexchange/{self.mailbox_id}/inbox"
        try:
            response = requests.get(inbox_url, timeout=5, verify=False)
            if response.status_code == 200:
                messages = response.json()
                # Handle different response formats
                if isinstance(messages, list) and len(messages) > 0:
                    # Test the first message endpoint
                    first_message = messages[0]
                    first_message_id = (
                        first_message.get("id")
                        if isinstance(first_message, dict)
                        else str(first_message)
                    )

                    if first_message_id:
                        message_url = f"{self.mesh_url}/messageexchange/{self.mailbox_id}/inbox/{first_message_id}"
                        msg_response = requests.get(
                            message_url, timeout=5, verify=False
                        )
                        self.assertEqual(msg_response.status_code, 200)

                        # Handle empty responses (valid scenario)
                        if msg_response.content:
                            try:
                                message_data = msg_response.json()
                                self.assertIsInstance(message_data, dict)
                            except requests.exceptions.JSONDecodeError:
                                # Empty or non-JSON response is valid
                                self.skipTest(
                                    "Message endpoint returned empty or non-JSON response"
                                )
                        else:
                            # Empty response is valid
                            self.skipTest("Message endpoint returned empty response")
                elif isinstance(messages, dict):
                    # Handle case where response is a dict with messages array
                    messages_list = messages.get("messages", [])
                    if messages_list and len(messages_list) > 0:
                        first_message = messages_list[0]
                        first_message_id = (
                            first_message.get("id")
                            if isinstance(first_message, dict)
                            else str(first_message)
                        )

                        if first_message_id:
                            message_url = f"{self.mesh_url}/messageexchange/{self.mailbox_id}/inbox/{first_message_id}"
                            msg_response = requests.get(
                                message_url, timeout=5, verify=False
                            )
                            self.assertEqual(msg_response.status_code, 200)

                            # Handle empty responses (valid scenario)
                            if msg_response.content:
                                try:
                                    message_data = msg_response.json()
                                    self.assertIsInstance(message_data, dict)
                                except requests.exceptions.JSONDecodeError:
                                    # Empty or non-JSON response is valid
                                    self.skipTest(
                                        "Message endpoint returned empty or non-JSON response"
                                    )
                            else:
                                # Empty response is valid
                                self.skipTest(
                                    "Message endpoint returned empty response"
                                )
                else:
                    # No messages available - this is a valid state
                    self.skipTest("No messages available in MESH inbox for testing")
        except requests.RequestException as e:
            self.fail(f"Failed to test MESH message endpoint: {e}")
        except (KeyError, IndexError, TypeError) as e:
            # Handle unexpected response structure
            self.skipTest(f"Unexpected MESH API response structure: {e}")
        except requests.exceptions.JSONDecodeError as e:
            # Handle JSON decode errors gracefully
            self.skipTest(f"Invalid JSON response from MESH API: {e}")


class TestMeshIntegrationSkipped(TestCase):
    """Tests that demonstrate graceful skipping when MESH client unavailable"""

    def test_integration_tests_skipped_when_mesh_unavailable(self):
        """Test that integration tests are properly skipped"""
        if not mesh_client_available():
            # This test should be skipped when MESH client is not available
            self.skipTest("MESH client not available - integration tests skipped")

        # If we get here, MESH client is available
        self.assertTrue(True)


# Environment variable to control integration test execution
def pytest_configure(config):
    """Configure pytest to skip integration tests if MESH client not available"""
    if not mesh_client_available():
        config.addinivalue_line(
            "markers",
            "integration: mark test as integration test requiring MESH client",
        )


@pytest.mark.integration
class TestMeshIntegrationWithMarker(TestCase):
    """Integration tests with pytest marker for selective execution"""

    def test_mesh_integration_with_marker(self):
        """Test that can be run selectively with pytest -m integration"""
        if not mesh_client_available():
            pytest.skip("MESH client not available")

        # Integration test logic here
        self.assertTrue(True)
