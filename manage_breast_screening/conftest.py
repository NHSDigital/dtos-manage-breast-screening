from unittest import TestCase

import pytest
from django.test.client import Client

from manage_breast_screening.auth.tests.factories import UserFactory

# Show long diffs in failed test output
TestCase.maxDiff = None


@pytest.fixture
def user():
    return UserFactory.create(nhs_uid="user1")


@pytest.fixture
def administrative_user():
    return UserFactory.create(nhs_uid="administrative1", groups__administrative=True)


@pytest.fixture
def clinical_user():
    return UserFactory.create(nhs_uid="clinical1", groups__clinical=True)


@pytest.fixture
def superuser():
    return UserFactory.create(nhs_uid="superuser1", groups__superuser=True)


@pytest.fixture
def clinical_user_client(clinical_user):
    client = Client()
    client.force_login(clinical_user)
    return client


@pytest.fixture
def administrative_user_client(administrative_user):
    client = Client()
    client.force_login(administrative_user)
    return client


@pytest.fixture
def superuser_client(superuser):
    client = Client()
    client.force_login(superuser)
    return client
