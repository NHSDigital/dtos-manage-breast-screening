import re

import pytest
from django.shortcuts import redirect
from django.urls import reverse
from playwright.sync_api import expect

from .system_test_setup import SystemTestCase


class TestCIS2SignIn(SystemTestCase):
    @pytest.fixture(autouse=True)
    def setup_oauth_stub(self, settings, monkeypatch):
        class FakeCIS2Client:
            def authorize_redirect(self, request, redirect_uri, acr_values):
                # Simulate CIS2 redirecting back to our callback with an auth code
                return redirect(
                    f"{redirect_uri}?code=fake-code&acr_values={acr_values}"
                )

            def authorize_access_token(self, request):
                # Simulate exchanging the code for tokens + OIDC userinfo
                return {
                    "access_token": "fake-access-token",
                    "token_type": "Bearer",
                    "id_token": "fake-id-token",
                }

            def userinfo(self, token=None):
                # Simulate retrieving user info from the OIDC provider
                return {
                    "sub": "cis2-user-1",
                    "email": "jane.doe@example.com",
                    "given_name": "Jane",
                    "family_name": "Doe",
                }

        # Patch the view-layer reference so both sign-in and callback use the fake
        monkeypatch.setattr(
            "manage_breast_screening.auth.views.get_cis2_client",
            lambda: FakeCIS2Client(),
        )

    def test_sign_in_and_sign_out_via_cis2(self):
        self.given_i_am_on_the_log_in_page()
        self.when_i_log_in_via_cis2()
        self.then_i_am_redirected_to_home()
        self.then_header_shows_log_out()
        self.when_i_click_log_out()
        self.then_header_shows_log_in()

    def given_i_am_on_the_log_in_page(self):
        self.page.goto(self.live_server_url + reverse("auth:sign_in"))

    def when_i_log_in_via_cis2(self):
        self.page.get_by_text("Log in with CIS2").click()

    def then_i_am_redirected_to_home(self):
        home_path = reverse("clinics:index")
        expect(self.page).to_have_url(re.compile(home_path))

    def then_header_shows_log_out(self):
        header = self.page.get_by_role("navigation")
        expect(header.get_by_text("Log out")).to_be_visible()

    def when_i_click_log_out(self):
        header = self.page.get_by_role("navigation")
        header.get_by_text("Log out").click()

    def then_header_shows_log_in(self):
        header = self.page.get_by_role("navigation")
        expect(header.get_by_text("Log in")).to_be_visible()
