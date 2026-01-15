from unittest.mock import ANY, Mock

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import override_settings
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
@override_settings(CIS2_ACR_VALUES="some-test-acr-value")
def test_cis2_login_uses_configured_acr_values(client, monkeypatch):
    mock_client = Mock()
    mock_redirect_response = HttpResponse(status=302)
    mock_redirect_response["Location"] = "https://cis2.example.com/authorize"
    mock_client.authorize_redirect.return_value = mock_redirect_response
    monkeypatch.setattr(
        "manage_breast_screening.auth.views.get_cis2_client",
        lambda: mock_client,
    )
    monkeypatch.setattr(
        "manage_breast_screening.auth.views.cis2_redirect_uri",
        lambda: "https://testserver/auth/cis2/callback",
    )

    client.get(reverse("auth:cis2_login"))

    mock_client.authorize_redirect.assert_called_once_with(
        ANY,
        "https://testserver/auth/cis2/callback",
        acr_values="some-test-acr-value",
    )


@pytest.mark.django_db
class TestCis2Callback:
    @pytest.fixture
    def mock_cis2_client_factory(self, monkeypatch):
        """Factory fixture for creating and configuring mock CIS2 clients."""

        def _create_mock_client(
            id_token_sub="user-123",
            userinfo_sub="user-123",
            id_assurance_level=3,
            authentication_assurance_level=3,
        ):
            mock_client = Mock()
            mock_client.authorize_access_token.return_value = {
                "userinfo": {
                    "sub": id_token_sub,
                    "id_assurance_level": id_assurance_level,
                    "authentication_assurance_level": authentication_assurance_level,
                },
            }
            mock_client.userinfo.return_value = {"sub": userinfo_sub}

            monkeypatch.setattr(
                "manage_breast_screening.auth.views.get_cis2_client",
                lambda: mock_client,
            )
            return mock_client

        return _create_mock_client

    def test_rejects_mismatched_sub(self, client, mock_cis2_client_factory):
        """Test that cis2_callback returns 400 when sub from userinfo doesn't match sub from ID token."""
        mock_cis2_client_factory(
            id_token_sub="user-123",
            userinfo_sub="user-456",
        )

        response = client.get(reverse("auth:cis2_callback"))

        assert response.status_code == 400
        assert b"Subject mismatch in CIS2 response" in response.content

    @pytest.mark.parametrize(
        "acr_values,id_level,auth_level,expected_error",
        [
            ("AAL2_OR_AAL3_ANY", 2, 2, b"Insufficient identity assurance level"),
            ("AAL2_OR_AAL3_ANY", 3, 1, b"Insufficient authentication assurance level"),
            ("AAL3_ANY", 3, 2, b"Insufficient authentication assurance level"),
        ],
        ids=[
            "id_assurance_level_too_low",
            "auth_assurance_level_too_low_for_aal2",
            "auth_assurance_level_too_low_for_aal3",
        ],
    )
    def test_rejects_insufficient_assurance_levels(
        self,
        client,
        mock_cis2_client_factory,
        acr_values,
        id_level,
        auth_level,
        expected_error,
    ):
        """Test that cis2_callback rejects authentication when assurance levels are insufficient."""
        with override_settings(CIS2_ACR_VALUES=acr_values):
            mock_cis2_client_factory(
                id_assurance_level=id_level,
                authentication_assurance_level=auth_level,
            )

            response = client.get(reverse("auth:cis2_callback"))

            assert response.status_code == 403
            assert expected_error in response.content

    @pytest.mark.parametrize(
        "acr_values,id_level,auth_level",
        [
            ("AAL2_OR_AAL3_ANY", 3, 2),
            ("AAL3_ANY", 3, 3),
            ("AAL3_ANY", "3", "3"),
        ],
        ids=[
            "aal2_valid",
            "aal3_valid",
            "levels_provided_as_strings",
        ],
    )
    def test_accepts_valid_assurance_levels(
        self,
        client,
        monkeypatch,
        mock_cis2_client_factory,
        acr_values,
        id_level,
        auth_level,
    ):
        """Test that cis2_callback accepts valid assurance levels."""
        with override_settings(CIS2_ACR_VALUES=acr_values):
            mock_cis2_client_factory(
                id_assurance_level=id_level,
                authentication_assurance_level=auth_level,
            )

            mock_user = Mock()
            mock_user.nhs_uid = "user-123"
            mock_authenticate = Mock(return_value=mock_user)
            mock_login = Mock()

            monkeypatch.setattr(
                "manage_breast_screening.auth.views.authenticate",
                mock_authenticate,
            )
            monkeypatch.setattr(
                "manage_breast_screening.auth.views.auth_login",
                mock_login,
            )

            response = client.get(reverse("auth:cis2_callback"))

            assert response.status_code == 302
            assert "/clinics/select-provider" in response.headers["location"]

            mock_authenticate.assert_called_once_with(
                ANY, cis2_sub="user-123", cis2_userinfo={"sub": "user-123"}
            )
            mock_login.assert_called_once_with(ANY, mock_user)
