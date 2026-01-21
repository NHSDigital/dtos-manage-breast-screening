from types import SimpleNamespace
from unittest import TestCase

import pytest
from django.test.client import Client

from manage_breast_screening.clinics.tests.factories import (
    ProviderFactory,
    UserAssignmentFactory,
)
from manage_breast_screening.users.tests.factories import UserFactory

# Show long diffs in failed test output
TestCase.maxDiff = None


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
def clinical_user_client(clinical_user, current_provider):
    client = Client()
    client.force_login(clinical_user)
    session = client.session
    session["current_provider"] = str(current_provider.pk)
    session.save()
    return SimpleNamespace(
        http=client, current_provider=current_provider, user=clinical_user
    )


@pytest.fixture
def administrative_user_client(administrative_user, current_provider):
    client = Client()
    client.force_login(administrative_user)
    session = client.session
    session["current_provider"] = str(current_provider.pk)
    session.save()
    return SimpleNamespace(
        http=client, current_provider=current_provider, user=administrative_user
    )
