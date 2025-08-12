import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from ..models import ANNA, CHLOE


@pytest.fixture
def group():
    return Group.objects.create(name="group")


@pytest.fixture(autouse=True)
def anna(group):
    user = get_user_model().objects.create(
        username=ANNA.username, first_name=ANNA.first_name, last_name=ANNA.last_name
    )
    user.groups.add(group)
    return user


@pytest.fixture(autouse=True)
def chloe(group):
    user = get_user_model().objects.create(
        username=CHLOE.username, first_name=CHLOE.first_name, last_name=CHLOE.last_name
    )
    user.groups.add(group)
    return user


@pytest.mark.django_db
def test_get_persona_login(client):
    response = client.get(
        reverse("demo:persona_login"),
        query_params={"next": "/some-url"},
    )
    assert response.status_code == 200

    assertInHTML("Anna Davies", response.text)
    assertInHTML("Chloë Robinson", response.text)
    assertInHTML('<input type="hidden" name="next" value="/some-url">', response.text)


@pytest.mark.django_db
def test_post_persona_login(client):
    response = client.post(
        reverse("demo:persona_login"),
        {"username": "anna_davies", "next": "/some-url"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/some-url"


@pytest.mark.django_db
def test_bad_redirect(client):
    response = client.post(
        reverse("demo:persona_login"),
        {"username": "anna_davies", "next": "http://evil.com"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/demo/persona-login/"
