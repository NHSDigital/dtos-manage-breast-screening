from unittest import TestCase

import pytest
from django.test.client import Client

from manage_breast_screening.auth.models import Role
from manage_breast_screening.auth.tests.factories import UserFactory
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory

# Show long diffs in failed test output
TestCase.maxDiff = None


@pytest.fixture
def user():
    return UserFactory.create(nhs_uid="user1")


@pytest.fixture
def administrative_user():
    user = UserFactory.create(nhs_uid="administrative1")
    UserAssignmentFactory.create(user=user, roles=[Role.ADMINISTRATIVE])
    return user


@pytest.fixture
def clinical_user():
    user = UserFactory.create(nhs_uid="clinical1")
    UserAssignmentFactory.create(user=user, roles=[Role.CLINICAL])
    return user


@pytest.fixture
def clinical_user_client(clinical_user):
    client = Client()
    client.force_login(clinical_user)
    provider = clinical_user.assignments.first().provider
    session = client.session
    session["current_provider"] = str(provider.pk)
    session.save()
    return client


@pytest.fixture
def administrative_user_client(administrative_user):
    client = Client()
    client.force_login(administrative_user)
    provider = administrative_user.assignments.first().provider
    session = client.session
    session["current_provider"] = str(provider.pk)
    session.save()
    return client
