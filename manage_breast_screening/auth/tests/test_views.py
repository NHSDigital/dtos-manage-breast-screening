from unittest.mock import ANY, Mock

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import override_settings
from django.urls import reverse
from pytest_django.asserts import assertInHTML

from manage_breast_screening.clinics.tests.factories import UserAssignmentFactory


@pytest.fixture(autouse=True)
def demo_users():
    User = get_user_model()
    for first_name, last_name, role in [
        ("Anna", "Davies", "administrative"),
        ("Chloë", "Robinson", "clinical"),
        ("Olivia", "Morgan", "administrative"),
        ("Ella", "Foster", "clinical"),
    ]:
        user = User.objects.create(
            nhs_uid=f"{first_name.lower()}_{last_name.lower()}",
            first_name=first_name,
            last_name=last_name,
        )
        UserAssignmentFactory(user=user, **{role: True})

    User.objects.create(
        nhs_uid="priya_bains",
        first_name="Priya",
        last_name="Bains",
        is_superuser=True,
        is_staff=True,
    )


@pytest.mark.django_db
def test_get_persona_login(client):
    response = client.get(
        reverse("auth:persona_login"),
        query_params={"next": "/some-url"},
    )
    assert response.status_code == 200

    assertInHTML("Anna Davies", response.text)
    assertInHTML("Chloë Robinson", response.text)
    assertInHTML("Olivia Morgan", response.text)
    assertInHTML("Ella Foster", response.text)
    assertInHTML('<input type="hidden" name="next" value="/some-url">', response.text)


@pytest.mark.django_db
def test_post_persona_login(client):
    response = client.post(
        reverse("auth:persona_login"),
        {"username": "anna_davies", "next": "/some-url"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/current-provider/select/?next=%2Fsome-url"


@pytest.mark.django_db
def test_post_persona_login_superuser_redirects_to_admin(client):
    response = client.post(
        reverse("auth:persona_login"),
        {"username": "priya_bains"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/"


@pytest.mark.django_db
def test_post_persona_login_superuser_with_root_next_redirects_to_admin(client):
    response = client.post(
        reverse("auth:persona_login"),
        {"username": "priya_bains", "next": "/"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/admin/"


@pytest.mark.django_db
def test_post_persona_login_superuser_with_next_redirects_to_select_provider(client):
    response = client.post(
        reverse("auth:persona_login"),
        {"username": "priya_bains", "next": "/some-url"},
    )
    assert response.status_code == 302
    assert response.headers["location"] == "/current-provider/select/?next=%2Fsome-url"


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
            ("AAL3_ANY", None, 3, b"Insufficient identity assurance level"),
            ("AAL3_ANY", 3, None, b"Insufficient authentication assurance level"),
        ],
        ids=[
            "id_assurance_level_too_low",
            "auth_assurance_level_too_low_for_aal2",
            "auth_assurance_level_too_low_for_aal3",
            "id_assurance_level_none",
            "auth_assurance_level_none",
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
            mock_user.is_superuser = False
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
            assert "/current-provider/select/" in response.headers["location"]

            mock_authenticate.assert_called_once_with(
                ANY, cis2_sub="user-123", cis2_userinfo={"sub": "user-123"}
            )
            mock_login.assert_called_once_with(ANY, mock_user)

    def test_superuser_redirects_to_admin(
        self, client, monkeypatch, mock_cis2_client_factory
    ):
        """Superusers should always be sent to the admin site after login."""
        mock_cis2_client_factory()

        mock_user = Mock()
        mock_user.nhs_uid = "user-123"
        mock_user.is_superuser = True

        monkeypatch.setattr(
            "manage_breast_screening.auth.views.authenticate",
            Mock(return_value=mock_user),
        )
        monkeypatch.setattr("manage_breast_screening.auth.views.auth_login", Mock())

        response = client.get(reverse("auth:cis2_callback"))

        assert response.status_code == 302
        assert response.headers["location"] == "/admin/"


@pytest.mark.django_db
class TestJwksView:
    def test_returns_single_key_when_only_current_key_configured(self, client):
        response = client.get(reverse("auth:jwks"))

        assert response.status_code == 200
        keys = response.json()["keys"]
        assert len(keys) == 1
        assert keys[0]["kty"] == "RSA"
        assert keys[0]["use"] == "sig"
        assert keys[0]["alg"] == "RS512"
        assert "kid" in keys[0]

    @override_settings(CIS2_OLD_PRIVATE_KEY=settings.CIS2_CLIENT_PRIVATE_KEY)
    def test_returns_two_keys_when_old_key_configured(self, client):
        response = client.get(reverse("auth:jwks"))

        assert response.status_code == 200
        keys = response.json()["keys"]
        assert len(keys) == 2
        assert all(k["kty"] == "RSA" for k in keys)

    def test_returns_500_on_error(self, client, monkeypatch):
        monkeypatch.setattr(
            "manage_breast_screening.auth.views.public_jwk_from_rsa_private_key",
            Mock(side_effect=Exception("boom")),
        )

        response = client.get(reverse("auth:jwks"))

        assert response.status_code == 500
        assert response.json() == {"keys": []}
