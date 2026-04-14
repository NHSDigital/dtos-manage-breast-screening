from datetime import datetime
from datetime import timezone as tz
from types import SimpleNamespace
from unittest import TestCase

import pytest
from django.test.client import Client
from django.utils import timezone
from openfeature import api
from openfeature.provider.in_memory_provider import InMemoryFlag, InMemoryProvider

from manage_breast_screening.clinics.tests.factories import (
    ProviderFactory,
    UserAssignmentFactory,
)
from manage_breast_screening.core.apps import _FLAGS_YAML
from manage_breast_screening.core.feature_flags import setup_feature_flags
from manage_breast_screening.users.tests.factories import UserFactory

# Show long diffs in failed test output
TestCase.maxDiff = None


@pytest.fixture
def with_flag_enabled():
    """Enable a named boolean OpenFeature flag for the duration of a test.

    Usage::

        def test_something(with_flag_enabled):
            with_flag_enabled("my_flag")
            ...
    """

    enabled_flags = {}

    def enable(flag_name: str):
        enabled_flags[flag_name] = InMemoryFlag(
            default_variant="on",
            variants={"on": True, "off": False},
        )
        api.set_provider(InMemoryProvider(enabled_flags))

    yield enable

    setup_feature_flags(_FLAGS_YAML)


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
def another_clinical_user(current_provider):
    user = UserFactory.create(nhs_uid="clinical2")
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


@pytest.fixture
def known_datetime(time_machine):
    """
    Eliminate non-determinism caused by the current time, due to things
    like the display of relative dates.
    """
    dt = datetime(2025, 1, 1, 10, tzinfo=tz.utc)
    time_machine.move_to(dt)
    return dt
