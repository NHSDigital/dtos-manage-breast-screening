import pytest
from django.urls import reverse

from manage_breast_screening.participants.tests.factories import ParticipantFactory


@pytest.fixture
def participant():
    return ParticipantFactory.create()


@pytest.mark.django_db
class TestShowParticipant:
    def test_renders_response(self, client, participant):
        response = client.get(
            reverse("participants:show", kwargs={"pk": participant.pk}),
        )
        assert response.status_code == 200
