from unittest.mock import Mock

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


@pytest.mark.django_db
def test_cis2_callback_rejects_mismatched_sub(client, monkeypatch):
    """Test that cis2_callback returns 400 when sub from userinfo doesn't match sub from ID token."""
    mock_client = Mock()
    mock_client.authorize_access_token.return_value = {
        "userinfo": {"sub": "user-123"},
        "access_token": "fake-token",
    }
    mock_client.userinfo.return_value = {"sub": "user-456"}

    monkeypatch.setattr(
        "manage_breast_screening.auth.views.get_cis2_client",
        lambda: mock_client,
    )

    response = client.get(reverse("auth:cis2_callback"))

    assert response.status_code == 400
    assert b"Subject mismatch in CIS2 response" in response.content
