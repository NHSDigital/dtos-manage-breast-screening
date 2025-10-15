import pytest
from django.urls import reverse

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
)


@pytest.mark.django_db
class TestShowParticipant:
    def test_renders_response(self, clinical_user_client):
        # Create an appointment with the current provider so the participant is accessible
        participant = ParticipantFactory.create()
        AppointmentFactory.create(
            screening_episode__participant=participant,
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
        )
        response = clinical_user_client.http.get(
            reverse("participants:show", kwargs={"pk": participant.pk}),
        )
        assert response.status_code == 200
