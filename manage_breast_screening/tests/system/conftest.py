from collections import Counter

import pytest
from django.test.client import Client
from django.utils import timezone
from pytest_bdd import given, then
from pytest_bdd.parsers import parse

from manage_breast_screening.core.utils.accessibility import AxeAdapter


@pytest.fixture
def axe():
    return AxeAdapter()


@pytest.fixture
def get_user_for_role(request):
    def fn(role):
        if role == "an administrative user":
            fixture = "administrative_user"
        elif role == "a clinical user":
            fixture = "clinical_user"
        else:
            raise ValueError(role)
        return request.getfixturevalue(fixture)

    return fn


@given(parse("I am logged in as {role}"), target_fixture="session")
def login_as(role, get_user_for_role, context, live_server):
    """
    Emulate logging in as a particular user, without needing
    to visit a login page.
    """
    user = get_user_for_role(role)

    # Fake a login
    client = Client()
    client.force_login(user)

    session = client.session
    session["login_time"] = timezone.now().isoformat()

    assignment = user.assignments.first()
    if assignment:
        session["current_provider"] = str(assignment.provider_id)

    session.save()

    # Transfer the session cookie to the playwright browser
    sessionid = client.cookies["sessionid"].value
    context.add_cookies(
        [
            {
                "name": "sessionid",
                "value": sessionid,
                "url": live_server.url,
                "httpOnly": True,
            }
        ]
    )

    return session


@then("the accessibility baseline is met")
def then_the_accessibility_baseline_is_met(axe, page, require_unique_link_text=True):
    """
    Check for certain accessibility issues that can be detected automatically without
    context of the page under test.

    If require_unique_link_text is True (the default), then fail if there are
    any links on the page with identical link text (or any buttons styled to
    look like links). This depends on context, but generally we should be disambiguating
    any interactive elements that appear close together, and avoiding any non-specific
    links like "click here".
    """
    page.wait_for_selector("main")
    results = axe.run(page=page)
    assert results.violations_count == 0, results.generate_report()

    if require_unique_link_text:
        links = page.get_by_role("link").or_(page.locator("css=.app-link"))

        counter = Counter(link.text_content().strip() for link in links.all())

        duplicates = {k: v for k, v in counter.items() if v > 1}

        assert len(duplicates) == 0, duplicates
