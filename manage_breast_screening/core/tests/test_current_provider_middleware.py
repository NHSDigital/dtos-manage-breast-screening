import pytest
from django.urls import reverse

from manage_breast_screening.clinics.models import Provider
from manage_breast_screening.core.tests.factories import UserFactory


@pytest.mark.django_db
def test_redirects_when_current_provider_missing(client):
    user = UserFactory()
    client.force_login(user)

    response = client.get(reverse("clinics:index"))

    assert response.status_code == 302
    assert response.headers["Location"] == reverse("clinics:select_provider")


@pytest.mark.django_db
def test_allows_request_when_current_provider_present(client):
    user = UserFactory()
    provider = Provider.objects.create(name="Test Provider")
    client.force_login(user)

    session = client.session
    session["current_provider"] = str(provider.pk)
    session.save()

    response = client.get(reverse("clinics:index"))

    assert response.status_code == 200
