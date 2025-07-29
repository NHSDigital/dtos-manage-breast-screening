import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTestEnvironmentLogin:
    @pytest.fixture(autouse=True)
    def setup(self, set_basic_auth_credentials):
        pass

    def test_basic_auth_challenge(self, client):
        response = client.get(reverse("test_login"))
        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Basic realm=''"

    def test_valid_login(self, client, basic_auth_valid_authorization_token):
        response = client.get(
            reverse("test_login"),
            headers={"Authorization": basic_auth_valid_authorization_token},
        )
        assert response.status_code == 302
        assert response.url == "/"

    def test_invalid_login(self, client):
        response = client.get(
            reverse("test_login"),
            headers={"Authorization": ""},
        )
        assert response.status_code == 403

    def test_redirect_if_already_logged_in(self, client, user):
        client.force_login(user)
        response = client.get(reverse("test_login"))
        assert response.status_code == 302
        assert response.url == "/"
