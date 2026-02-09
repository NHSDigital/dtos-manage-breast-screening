import pytest
from django.urls import reverse

from manage_breast_screening.participants.tests.factories import AppointmentFactory


@pytest.mark.django_db
class TestShowAppointment:
    def test_renders_response(self, clinical_user_client):
        appointment = AppointmentFactory.create(
            clinic_slot__clinic__setting__provider=clinical_user_client.current_provider
        )
        response = clinical_user_client.http.get(
            reverse(
                "mammograms:show_appointment",
                kwargs={"pk": appointment.pk},
            )
        )
        assert response.status_code == 200
