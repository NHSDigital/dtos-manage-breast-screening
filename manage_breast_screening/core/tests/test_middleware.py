import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestBasicAuthMiddleware:
    @pytest.fixture(
        autouse=True,
    )
    def setup(self, set_basic_auth_credentials, settings):
        settings.MIDDLEWARE = [
            "manage_breast_screening.core.middleware.BasicAuthMiddleware",
        ]

    def test_basic_auth_challenge(self, client):
        response = client.get(reverse("clinics:index"))
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic realm=''"

    def test_valid_login(self, client, basic_auth_valid_authorization_token):
        response = client.get(
            reverse("clinics:index"),
            headers={"Authorization": basic_auth_valid_authorization_token},
        )
        assert response.status_code == 200

    def test_invalid_login(self, client):
        response = client.get(
            reverse("clinics:index"),
            headers={"Authorization": ""},
        )
        assert response.status_code == 403

    def test_basic_auth_disabled(self, client, settings):
        settings.BASIC_AUTH_ENABLED = False
        response = client.get(
            reverse("clinics:index"),
            headers={"Authorization": ""},
        )
        assert response.status_code == 200
