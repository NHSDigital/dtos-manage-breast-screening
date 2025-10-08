import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from manage_breast_screening.auth.models import ADMINISTRATIVE_PERSONA, CLINICAL_PERSONA
from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory


@pytest.fixture(autouse=True)
def anna():
    user = get_user_model().objects.create(
        nhs_uid=ADMINISTRATIVE_PERSONA.username,
        first_name=ADMINISTRATIVE_PERSONA.first_name,
        last_name=ADMINISTRATIVE_PERSONA.last_name,
    )
    UserAssignmentFactory(user=user, administrative=True)
    return user


@pytest.fixture(autouse=True)
def chloe():
    user = get_user_model().objects.create(
        nhs_uid=CLINICAL_PERSONA.username,
        first_name=CLINICAL_PERSONA.first_name,
        last_name=CLINICAL_PERSONA.last_name,
    )
    UserAssignmentFactory(user=user, clinical=True)
    return user


@pytest.mark.django_db
def test_get_persona_login(client):
    response = client.get(
        reverse("auth:persona_login"),
        query_params={"next": "/some-url"},
    )
    assert response.status_code == 200

    assertInHTML("Anna Davies", response.text)
    assertInHTML("Chloë Robinson", response.text)
    assertInHTML('<input type="hidden" name="next" value="/some-url">', response.text)


@pytest.mark.django_db
def test_post_persona_login(client):
    response = client.post(
        reverse("auth:persona_login"),
        {"username": "anna_davies", "next": "/some-url"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/clinics/select-provider/?next=%2Fsome-url"
