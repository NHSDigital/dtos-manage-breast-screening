import pytest
from django.urls import reverse

from manage_breast_screening.conftest import force_mbs_login
from manage_breast_screening.users.tests.factories import UserFactory

from .factories import ProviderFactory, UserAssignmentFactory


class TestSelectProvider:
    @pytest.mark.django_db
    def test_single_assignment_redirects_to_next(self, client):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider, clinical=True)

        force_mbs_login(client, user)

        response = client.get(
            reverse("select_provider"), {"next": "/clinics/some-target/"}
        )

        assert response.status_code == 302
        assert response["Location"] == "/clinics/some-target/"
        assert client.session["current_provider"] == str(provider.pk)

    @pytest.mark.django_db
    def test_provider_select_post_redirects_to_next(self, client):
        user = UserFactory()
        provider1 = ProviderFactory()
        provider2 = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider1, clinical=True)
        UserAssignmentFactory(user=user, provider=provider2, clinical=True)

        force_mbs_login(client, user)

        response = client.post(
            reverse("select_provider"),
            {"provider": provider2.pk, "next": "/clinics/other-target/"},
        )

        assert response.status_code == 302
        assert response["Location"] == "/clinics/other-target/"
        assert client.session["current_provider"] == str(provider2.pk)

    @pytest.mark.django_db
    def test_superuser_selects_any_provider(self, client):
        user = UserFactory(is_superuser=True)
        ProviderFactory()
        provider2 = ProviderFactory()

        force_mbs_login(client, user)

        response = client.post(
            reverse("select_provider"),
            {"provider": provider2.pk, "next": "/clinics/other-target/"},
        )

        assert response.status_code == 302
        assert response["Location"] == "/clinics/other-target/"
        assert client.session["current_provider"] == str(provider2.pk)

    @pytest.mark.django_db
    def test_safely_handles_bad_redirect(self, client):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider, clinical=True)

        force_mbs_login(client, user)

        response = client.post(
            reverse("select_provider"),
            {"provider": provider.pk, "next": "http://evil.com"},
        )

        assert response.status_code == 302
        assert response.headers["location"] == reverse("clinics:list_clinics")

    @pytest.mark.django_db
    def test_excludes_providers_with_no_roles(self, client):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider)

        force_mbs_login(client, user)

        response = client.get(reverse("select_provider"))

        assert response.status_code == 200
        assert "Your account is not recognised" in response.text


def login_with_provider(client, user, provider):
    force_mbs_login(client, user)
    session = client.session
    session["current_provider"] = str(provider.pk)
    session.save()


class TestProviderSettings:
    @pytest.mark.django_db
    def test_requires_sysadmin(self, client):
        user = UserFactory(is_superuser=False)
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider, administrative=True)

        login_with_provider(client, user, provider)

        response = client.get(reverse("update_provider_settings"))

        assert response.status_code == 403
        assert "You do not have permission" in response.text

    @pytest.mark.django_db
    def test_accessible_to_sysadmin(self, client):
        user = UserFactory(is_superuser=True)
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider)

        login_with_provider(client, user, provider)

        response = client.get(reverse("update_provider_settings"))

        assert response.status_code == 200
        assert "Settings" in response.text

    @pytest.mark.django_db
    def test_displays_provider_name(self, client):
        user = UserFactory(is_superuser=True)
        provider = ProviderFactory(name="Test Hospital Trust")
        UserAssignmentFactory(user=user, provider=provider)

        login_with_provider(client, user, provider)

        response = client.get(reverse("update_provider_settings"))

        assert "Test Hospital Trust" in response.text

    @pytest.mark.django_db
    def test_saves_settings(self, client):
        user = UserFactory(is_superuser=True)
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider)
        config = provider.get_config()
        assert config.manual_image_collection is True

        login_with_provider(client, user, provider)

        response = client.post(
            reverse("update_provider_settings"),
            {"manual_image_collection": ""},  # unchecked checkbox sends empty
        )

        assert response.status_code == 302
        config.refresh_from_db()
        assert config.manual_image_collection is False

    @pytest.mark.django_db
    def test_enables_manual_image_collection(self, client):
        user = UserFactory(is_superuser=True)
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider)
        config = provider.get_config()
        config.manual_image_collection = False
        config.save()

        login_with_provider(client, user, provider)

        response = client.post(
            reverse("update_provider_settings"),
            {"manual_image_collection": "true"},
        )

        assert response.status_code == 302
        config.refresh_from_db()
        assert config.manual_image_collection is True
