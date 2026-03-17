from types import SimpleNamespace
from unittest import TestCase

import pytest
from django.test.client import Client
from django.utils import timezone

from manage_breast_screening.clinics.tests.factories import (
    ProviderFactory,
    UserAssignmentFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory

# Show long diffs in failed test output
TestCase.maxDiff = None


def force_mbs_login(client, user):
    """Log in a user and set login_time to satisfy SessionTimeoutMiddleware."""
    client.force_login(user)
    session = client.session
    session["login_time"] = timezone.now().isoformat()
    session.save()


@pytest.fixture
def user():
    return UserFactory.create(nhs_uid="user1")


@pytest.fixture
def current_provider():
    return ProviderFactory.create()


@pytest.fixture
def administrative_user(current_provider):
    user = UserFactory.create(nhs_uid="administrative1")
    assignment = UserAssignmentFactory.create(
        user=user, administrative=True, provider=current_provider
    )
    assignment.make_current()
    return user


@pytest.fixture
def clinical_user(current_provider):
    user = UserFactory.create(nhs_uid="clinical1")
    assignment = UserAssignmentFactory.create(
        user=user, clinical=True, provider=current_provider
    )
    assignment.make_current()
    return user


@pytest.fixture
def superuser(current_provider):
    user = UserFactory.create(nhs_uid="superuser1", is_superuser=True)
    assignment = UserAssignmentFactory.create(
        user=user, administrative=True, provider=current_provider
    )
    assignment.make_current()
    return user


@pytest.fixture
def clinical_user_client(clinical_user, current_provider):
    client = Client()
    force_mbs_login(client, clinical_user)
    session = client.session
    session["current_provider"] = str(current_provider.pk)
    session.save()
    return SimpleNamespace(
        http=client, current_provider=current_provider, user=clinical_user
    )


@pytest.fixture
def administrative_user_client(administrative_user, current_provider):
    client = Client()
    force_mbs_login(client, administrative_user)
    session = client.session
    session["current_provider"] = str(current_provider.pk)
    session.save()
    return SimpleNamespace(
        http=client, current_provider=current_provider, user=administrative_user
    )


@pytest.fixture
def superuser_client(superuser, current_provider):
    client = Client()
    force_mbs_login(client, superuser)
    session = client.session
    session["current_provider"] = str(current_provider.pk)
    session.save()
    return SimpleNamespace(
        http=client, current_provider=current_provider, user=superuser
    )


# Pytest HTML Report customization for Jira markers
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store JIRA marker information in the test report."""
    outcome = yield
    report = outcome.get_result()

    # Add JIRA ticket to the report for display in HTML report
    jira_ticket = None
    for marker in item.iter_markers(name="jira"):
        if "ticket" in marker.kwargs:
            jira_ticket = marker.kwargs["ticket"]
            break

    # Add JIRA ticket as extra information in the HTML report
    if jira_ticket and report.when == "call":
        from pytest_html import extras

        # Store jira info in user_properties for the report
        report.user_properties.append(("jira_ticket", jira_ticket))

        # Add extras for HTML display
        if not hasattr(report, "extras"):
            report.extras = []

        report.extras.append(
            extras.html(f"<div><strong>JIRA Ticket:</strong> {jira_ticket}</div>")
        )
