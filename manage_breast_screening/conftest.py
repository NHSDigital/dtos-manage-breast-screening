import inspect
from html import escape
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
GITHUB_REPOSITORY_URL = "https://github.com/nhsdigital/dtos-manage-breast-screening"


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


# Pytest HTML Report customization for Jira and Risk markers
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store JIRA and Risk marker information in the test report."""
    outcome = yield
    report = outcome.get_result()

    # Add JIRA ticket to the report for display in HTML report
    jira_ticket = None
    for marker in item.iter_markers(name="jira"):
        if "ticket" in marker.kwargs:
            jira_ticket = marker.kwargs["ticket"]
            break

    # Add Risk ID to the report for display in HTML report
    risk_id = None
    for marker in item.iter_markers(name="risk"):
        if "id" in marker.kwargs:
            risk_id = marker.kwargs["id"]
            break

    # Store jira and risk info in user_properties
    if jira_ticket:
        report.user_properties.append(("jira_ticket", jira_ticket))
    if risk_id:
        report.user_properties.append(("risk_id", risk_id))

    test_docstring = inspect.cleandoc(item.obj.__doc__ or "")
    if test_docstring:
        report.user_properties.append(("test_docstring", test_docstring))


def pytest_html_results_table_row(report, cells):
    """Modify table row to show JIRA ticket and Risk ID in the Test column."""
    # Find jira ticket and risk id from user_properties
    jira_ticket = None
    risk_id = None
    test_docstring = None
    for name, value in report.user_properties:
        if name == "jira_ticket":
            jira_ticket = value
        elif name == "risk_id":
            risk_id = value
        elif name == "test_docstring":
            test_docstring = value

    if len(cells) <= 1:
        return

    test_file_path = report.nodeid.split("::")[0]
    source_url = f"{GITHUB_REPOSITORY_URL}/blob/main/{test_file_path}"
    source_link_html = (
        '<a class="test-source-link" '
        f'href="{escape(source_url)}" '
        'target="_blank" rel="noopener noreferrer">source</a>'
    )
    if len(cells) > 3:
        cells[3] = '<td class="col-links">' + source_link_html + "</td>"

    node_parts = report.nodeid.split("::")
    if len(node_parts) >= 3:
        display_test_id = "::".join(node_parts[-2:])
    elif len(node_parts) >= 2:
        display_test_id = node_parts[-1]
    else:
        display_test_id = report.nodeid

    display_test_html = f'<div class="test-name">{escape(display_test_id)}</div>'
    if test_docstring:
        display_test_html += (
            f'<div class="test-docstring">{escape(test_docstring)}</div>'
        )

    test_cell = cells[1].replace(report.nodeid, display_test_html)
    badges = []

    # Add JIRA badge if present
    if jira_ticket:
        badges.append(
            f'<span class="jira-badge report-marker-badge">{jira_ticket}</span>'
        )

    # Add Risk badge if present
    if risk_id:
        badges.append(f'<span class="risk-badge report-marker-badge">{risk_id}</span>')

    if badges:
        badges_html = "".join(badges)
        test_cell = test_cell.replace(
            '<td class="col-testId">', f'<td class="col-testId">{badges_html}'
        )

    cells[1] = test_cell
