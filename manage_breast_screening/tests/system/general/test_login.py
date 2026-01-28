import re
from datetime import timedelta

import pytest
import time_machine
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect
from qsessions.backends.db import SessionStore

from manage_breast_screening.clinics.tests.factories import (
    ProviderFactory,
    UserAssignmentFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory

from ..system_test_setup import SystemTestCase


class TestLogin(SystemTestCase):
    """
    System test for CIS2 login flow. This test uses a fake CIS2 OAuth client
    which mocks the function calls made by Authlib during the sign-in process.
    This allows us to test the sign-in flow without making actual calls to the
    CIS2 server.
    """

    def test_log_in_and_log_out_via_cis2(self):
        self.given_a_user_with_multiple_providers()
        self.given_i_am_on_the_home_page()
        self.then_header_shows_log_in()
        self.when_i_log_in_via_cis2()
        self.then_i_am_redirected_to_provider_selection()
        self.when_i_select_a_provider()
        self.then_i_am_redirected_to_home()
        self.then_header_shows_log_out()
        self.when_i_click_log_out()
        self.then_header_shows_log_in()

    def test_log_in_with_single_provider_assigned(self):
        self.given_a_user_with_single_provider()
        self.given_i_am_on_the_home_page()
        self.when_i_log_in_via_cis2()
        self.then_i_am_redirected_to_home()
        self.then_header_shows_log_out()

    def test_log_in_with_no_providers_assigned(self):
        self.given_a_user_with_no_providers()
        self.given_i_am_on_the_home_page()
        self.when_i_log_in_via_cis2()
        self.then_header_shows_log_out()
        self.then_i_see_no_providers_message()

    def test_session_expires_after_max_session_time(self):
        self.given_i_am_on_the_home_page()
        self.when_i_log_in_via_cis2()
        self.then_i_am_redirected_to_home()
        self.then_header_shows_log_out()
        self.and_i_am_logged_out_when_the_max_session_time_has_passed_even_if_i_have_been_active()

    def test_session_expires_after_inactivity_timeout_reached(self):
        self.given_i_am_on_the_home_page()
        self.when_i_log_in_via_cis2()
        self.then_i_am_redirected_to_home()
        self.then_header_shows_log_out()
        self.and_i_am_logged_out_after_inactivity_timeout()

    def given_a_user_with_no_providers(self):
        self.user = UserFactory(nhs_uid="cis2-user-1")

    def given_a_user_with_single_provider(self):
        self.user = UserFactory(nhs_uid="cis2-user-1")
        self.provider = ProviderFactory(name="Provider One")
        UserAssignmentFactory(user=self.user, provider=self.provider)

    def given_a_user_with_multiple_providers(self):
        self.user = UserFactory(nhs_uid="cis2-user-1")
        self.provider1 = ProviderFactory(name="Provider One")
        self.provider2 = ProviderFactory(name="Provider Two")

        UserAssignmentFactory(user=self.user, provider=self.provider1, clinical=True)
        UserAssignmentFactory(
            user=self.user, provider=self.provider2, administrative=True
        )

    def given_i_am_on_the_home_page(self):
        self.page.goto(self.live_server_url)

    def when_i_log_in_via_cis2(self):
        self.page.get_by_role("link", name="Log in").click()
        self.page.get_by_role("button", name="Log in with my Care Identity").click()

    def then_i_am_redirected_to_home(self):
        expect(self.page).to_have_url(re.compile(reverse("clinics:index")))

    def then_i_am_redirected_to_provider_selection(self):
        expect(self.page).to_have_url(re.compile(reverse("clinics:select_provider")))
        expect(self.page.get_by_text("Select your provider")).to_be_visible()
        expect(self.page.get_by_label("Provider One")).to_be_visible()
        expect(self.page.get_by_label("Provider Two")).to_be_visible()

    def when_i_select_a_provider(self):
        self.page.get_by_label("Provider One").click()
        self.page.get_by_role("button", name="Continue").click()

    def then_header_shows_log_out(self):
        header = self.page.get_by_role("navigation")
        expect(header.get_by_text("Log out")).to_be_visible()

    def when_i_click_log_out(self):
        header = self.page.get_by_role("navigation")
        header.get_by_text("Log out").click()

    def then_header_shows_log_in(self):
        header = self.page.get_by_role("navigation")

        expect(header.get_by_text("Log in")).to_be_visible()

    def then_i_see_no_providers_message(self):
        expect(self.page.get_by_text("Your account is not recognised")).to_be_visible()

    def then_i_am_on_the_login_page(self):
        expect(self.page).to_have_url(re.compile(reverse(settings.LOGIN_URL)))

    def and_i_am_logged_out_when_the_max_session_time_has_passed_even_if_i_have_been_active(
        self,
    ):
        User = get_user_model()
        user = User.objects.get(nhs_uid="cis2-user-1")
        session = user.session_set.filter(expire_date__gt=timezone.now()).first()
        assert session is not None

        plus_six_hours = timezone.now() + timedelta(hours=6)
        plus_twelve_hours = timezone.now() + timedelta(hours=12)

        # Simulate activity at +6 hours to avoid inactivity timeout
        self._update_session_activity(session, plus_six_hours)
        with time_machine.travel(plus_six_hours, tick=False):
            self.page.reload()
            self.then_header_shows_log_out()

        # Simulate activity just before +12 hours
        self._update_session_activity(session, plus_twelve_hours - timedelta(minutes=1))
        with time_machine.travel(plus_twelve_hours, tick=False):
            self.page.reload()
            self.then_i_am_on_the_login_page()

    def _update_session_activity(self, session, activity_time):
        store = SessionStore(session_key=session.session_key)
        store["last_activity"] = activity_time.isoformat()
        store.save()

    def and_i_am_logged_out_after_inactivity_timeout(self):
        before_timeout = timezone.now() + timedelta(minutes=14)
        with time_machine.travel(before_timeout, tick=False):
            self.page.reload()
            self.then_header_shows_log_out()  # Not logged out
            # Account for the 15-minute inactivity timeout plus the 1 minute update threshold
            after_timeout = timezone.now() + timedelta(minutes=16)
            with time_machine.travel(after_timeout, tick=False):
                self.page.reload()
                self.then_i_am_on_the_login_page()

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
                    "userinfo": {
                        "sub": "cis2-user-1",
                        "id_assurance_level": 3,
                        "authentication_assurance_level": 3,
                    },
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
