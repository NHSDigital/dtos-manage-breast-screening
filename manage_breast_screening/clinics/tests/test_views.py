import pytest
from django.urls import reverse

from manage_breast_screening.auth.models import Role

from .factories import ProviderFactory, UserAssignmentFactory, UserFactory


class TestSelectProvider:
    @pytest.mark.django_db
    def test_single_assignment_redirects_to_next(self, client):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider, roles=[Role.CLINICAL.value])

        client.force_login(user)

        response = client.get(
            reverse("clinics:select_provider"), {"next": "/clinics/some-target/"}
        )

        assert response.status_code == 302
        assert response["Location"] == "/clinics/some-target/"
        assert client.session["current_provider"] == str(provider.pk)

    @pytest.mark.django_db
    def test_provider_select_post_redirects_to_next(self, client):
        user = UserFactory()
        provider1 = ProviderFactory()
        provider2 = ProviderFactory()
        UserAssignmentFactory(
            user=user, provider=provider1, roles=[Role.CLINICAL.value]
        )
        UserAssignmentFactory(
            user=user, provider=provider2, roles=[Role.CLINICAL.value]
        )

        client.force_login(user)

        response = client.post(
            reverse("clinics:select_provider"),
            {"provider": provider2.pk, "next": "/clinics/other-target/"},
        )

        assert response.status_code == 302
        assert response["Location"] == "/clinics/other-target/"
        assert client.session["current_provider"] == str(provider2.pk)

    @pytest.mark.django_db
    def test_safely_handles_bad_redirect(self, client):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider, roles=[Role.CLINICAL.value])

        client.force_login(user)

        response = client.post(
            reverse("clinics:select_provider"),
            {"provider": provider.pk, "next": "http://evil.com"},
        )

        assert response.status_code == 302
        assert response.headers["location"] == reverse("clinics:index")

    @pytest.mark.django_db
    def test_excludes_providers_with_no_roles(self, client):
        user = UserFactory()
        provider = ProviderFactory()
        UserAssignmentFactory(user=user, provider=provider, roles=[])

        client.force_login(user)

        response = client.get(reverse("clinics:select_provider"))

        assert response.status_code == 200
        assert (
            "No providers found. Check that you've been assigned a role with at least one provider."
            in response.text
        )
