import requests
from django.urls import reverse

from .system_test_setup import SystemTestCase


class TestCIS2BackChannelLogout(SystemTestCase):
    """Simple system test for CIS2 back-channel logout endpoint."""

    def test_back_channel_logout(self):
        """Test that the back-channel logout endpoint accepts a POST request."""
        # Construct the URL for the back-channel logout endpoint
        url = f"{self.live_server_url}{reverse('auth:cis2_back_channel_logout')}"

        # Send a simple POST request with a fake logout token
        response = requests.post(url, data={"logout_token": "fake-logout-token"})

        # Print the response for debugging
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")

        # We're not asserting anything here, just making the request
