import os
import re
from collections import Counter

import pytest
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test.client import Client
from django.urls import reverse
from playwright.sync_api import expect, sync_playwright

from manage_breast_screening.auth.models import Role
from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.core.utils.acessibility import AxeAdapter


@pytest.mark.system
class SystemTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.browser.close()
        cls.playwright.stop()

    def setUp(self):
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_default_timeout(5000)
        self.axe = AxeAdapter(self.page)
        settings.BASE_URL = self.live_server_url

    def tearDown(self):
        self.page.close()

    def login_as_user(self, user: User):
        """
        Emulate logging in as a particular user, without needing
        to visit a login page.
        """
        # Fake a login
        client = Client()
        client.force_login(user)

        # Transfer the session cookie to the playwright browser
        sessionid = client.cookies["sessionid"].value
        self.context.add_cookies(
            [
                {
                    "name": "sessionid",
                    "value": sessionid,
                    "url": self.live_server_url,
                    "httpOnly": True,
                }
            ]
        )

    def login_as_role(self, role: Role):
        """
        Emulate logging in as a user having a particular role,
        without needing to visit a login page.
        """
        group, _created = Group.objects.get_or_create(name=role)
        user = UserFactory.create(groups=[group])
        self.login_as_user(user)

    def expect_url(self, url, **kwargs):
        path = reverse(url, kwargs=kwargs)
        url = re.compile(f"^{self.live_server_url}{re.escape(path)}$")
        expect(self.page).to_have_url(url)

    def expect_validation_error(
        self,
        error_text: str,
        fieldset_legend: str,
        field_label: str,
        field_name: str | None = "",
    ):
        summary_box = self.page.locator(".nhsuk-error-summary")
        expect(summary_box).to_contain_text(error_text)

        error_link = summary_box.get_by_text(error_text)
        error_link.click()

        fieldset = self.page.locator("fieldset").filter(has_text=fieldset_legend)
        error_span = fieldset.locator("span").filter(has_text=error_text)
        expect(error_span).to_contain_text(error_text)

        if field_name:
            field = fieldset.get_by_label(field_label).and_(
                fieldset.locator(f"[name='{field_name}']")
            )
        else:
            field = fieldset.get_by_label(field_label)

        expect(field).to_be_focused()

    def given_i_am_logged_in_as_a_clinical_user(self):
        self.login_as_role(Role.CLINICAL)

    def given_i_am_logged_in_as_an_administrative_user(self):
        self.login_as_role(Role.ADMINISTRATIVE)

    def given_i_am_logged_in_as_an_superuser(self):
        self.login_as_role(Role.SUPERUSER)

    def then_the_accessibility_baseline_is_met(self, require_unique_link_text=True):
        """
        Check for certain accessibility issues that can be detected automatically without
        context of the page under test.

        If require_unique_link_text is True (the default), then fail if there are
        any links on the page with identical link text (or any buttons styled to
        look like links). This depends on context, but generally we should be disambiguating
        any interactive elements that appear close together, and avoiding any non-specific
        links like "click here".
        """
        results = self.axe.run()
        self.assertEqual(results.violations_count, 0, results.generate_report())

        if require_unique_link_text:
            links = self.page.get_by_role("link").or_(
                self.page.locator("css=.app-button--link")
            )

            counter = Counter(link.text_content().strip() for link in links.all())

            # Known bug: There is an extra "home" link that is shown at mobile screen widths. This will be fixed in NHS.UK frontend 10.0.0
            counter["Home"] -= 1

            duplicates = {k: v for k, v in counter.items() if v > 1}

            self.assertEqual(len(duplicates), 0, duplicates)
