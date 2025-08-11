from unittest import TestCase

import pytest
from django.contrib.auth import get_user_model

# Show long diffs in failed test output
TestCase.maxDiff = None


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="user1", password="123")


@pytest.fixture
def logged_in_client(user, client):
    client.force_login(user)
    return client
