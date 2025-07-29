import pytest
from django.contrib.auth import get_user_model


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="user1", password="123")


@pytest.fixture
def logged_in_client(user, client):
    client.force_login(user)
    return client
