import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects

from manage_breast_screening.participants.tests.factories import (
    AppointmentFactory,
    ParticipantFactory,
)


@pytest.mark.django_db
class TestShowParticipant:
    def test_redirects_to_appointment_participant_details(self, clinical_user_client):
        # Create an appointment with the current provider so the participant is accessible
        participant = ParticipantFactory.create()
        appointment = AppointmentFactory.create(
            screening_episode__participant=participant,
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider,
        )
        response = clinical_user_client.http.get(
            reverse("participants:show", kwargs={"pk": participant.pk}),
        )

        assertRedirects(
            response,
            reverse(
                "mammograms:participant_details",
                kwargs={"pk": appointment.pk},
            ),
        )

    def test_redirects_to_home_if_no_appointment(self, clinical_user_client):
        participant = ParticipantFactory.create()

        response = clinical_user_client.http.get(
            reverse("participants:show", kwargs={"pk": participant.pk}),
        )

        assertRedirects(
            response,
            reverse("clinics:index"),
        )
